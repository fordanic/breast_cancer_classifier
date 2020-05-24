#!/bin/bash
INPUT_DATA_FOLDER='input_data/dcm'
OUTPUT_DATA_FOLDER='output_data/dcm'

DEVICE_TYPE='gpu'
GPU_NUMBER=0

function usage()
{
    echo "Run file to perform breast cancer classification according to model trained by Wu et al."
    echo "Read more in the paper Deep Neural Networks Improve Radiologists' Performance in Breast Cancer Screening"
    echo ""
    echo "./run.sh"
    echo "    -h --help"
    echo "    --input-data-folder=$INPUT_DATA_FOLDER"
    echo "    --output-data-folder=$OUTPUT_DATA_FOLDER"
    echo "    --device-type=$DEVICE_TYPE"
    echo "    --gpu-number=$GPU_NUMBER"
    echo ""
}

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
            ;;
        --input-data-folder)
            INPUT_DATA_FOLDER=$VALUE
            ;;
        --output-data-folder)
            OUTPUT_DATA_FOLDER=$VALUE
            ;;
        --device-type)
            DEVICE_TYPE=$VALUE
            ;;
        --gpu-number)
            GPU_NUMBER=$VALUE
            ;;
        *)
            echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
done

NUM_PROCESSES=10
NUM_EPOCHS=10
HEATMAP_BATCH_SIZE=100

DATA_FOLDER='temporary_data/images'
INITIAL_EXAM_LIST_PATH='temporary_data/exam_list_before_cropping.pkl'
PATCH_MODEL_PATH='models/sample_patch_model.p'
IMAGE_MODEL_PATH='models/sample_image_model.p'
IMAGEHEATMAPS_MODEL_PATH='models/sample_imageheatmaps_model.p'

CROPPED_IMAGE_PATH='temporary_data/cropped_images'
CROPPED_EXAM_LIST_PATH='temporary_data/cropped_images/cropped_exam_list.pkl'
EXAM_LIST_PATH='temporary_data/exam_list.pkl'
HEATMAPS_PATH='temporary_data/heatmaps'
IMAGEHEATMAPS_PREDICTIONS_PATH='temporary_data/imageheatmaps_predictions.csv'


export PYTHONPATH=$(pwd):$PYTHONPATH

echo 'Stage 0: Convert DICOM to PNG'
python3 src/utilities/prepare_dicom_images.py \
    --input-data-folder $INPUT_DATA_FOLDER \
    --output-data-folder $DATA_FOLDER \
    --exam-list-path $INITIAL_EXAM_LIST_PATH

echo 'Stage 1: Crop Mammograms'
python3 src/cropping/crop_mammogram.py \
    --input-data-folder $DATA_FOLDER \
    --output-data-folder $CROPPED_IMAGE_PATH \
    --exam-list-path $INITIAL_EXAM_LIST_PATH  \
    --cropped-exam-list-path $CROPPED_EXAM_LIST_PATH  \
    --num-processes $NUM_PROCESSES

echo 'Stage 2: Extract Centers'
python3 src/optimal_centers/get_optimal_centers.py \
    --cropped-exam-list-path $CROPPED_EXAM_LIST_PATH \
    --data-prefix $CROPPED_IMAGE_PATH \
    --output-exam-list-path $EXAM_LIST_PATH \
    --num-processes $NUM_PROCESSES

echo 'Stage 3: Generate Heatmaps'
python3 src/heatmaps/run_producer.py \
    --model-path $PATCH_MODEL_PATH \
    --data-path $EXAM_LIST_PATH \
    --image-path $CROPPED_IMAGE_PATH \
    --batch-size $HEATMAP_BATCH_SIZE \
    --output-heatmap-path $HEATMAPS_PATH \
    --device-type $DEVICE_TYPE \
    --gpu-number $GPU_NUMBER

echo 'Stage 4: Run Classifier (Image+Heatmaps)'
python3 src/modeling/run_model.py \
    --model-path $IMAGEHEATMAPS_MODEL_PATH \
    --data-path $EXAM_LIST_PATH \
    --image-path $CROPPED_IMAGE_PATH \
    --output-path $IMAGEHEATMAPS_PREDICTIONS_PATH \
    --use-heatmaps \
    --heatmaps-path $HEATMAPS_PATH \
    --use-augmentation \
    --num-epochs $NUM_EPOCHS \
    --device-type $DEVICE_TYPE \
    --gpu-number $GPU_NUMBER

echo 'Stage 5: Convert output to DICOM output'
python3 src/utilities/convert_results.py \
    INPUT_DATA_FOLDER \
    --heatmaps-path $HEATMAPS_PATH \
    --data-path $EXAM_LIST_PATH \
    --output-data-folder $OUTPUT_DATA_FOLDER
