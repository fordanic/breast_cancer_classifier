import os
import glob
import argparse
import pydicom

import src.utilities.pickling as pickling
import src.utilities.saving_images as saving_images

def find_view(dcm_files, laterality, view):
    for dcm_file in dcm_files:
        ds = pydicom.read_file(dcm_file)
        if ds.ImageLaterality == laterality and ds.ViewPosition == view:
            return dcm_file
    raise RuntimeError()

def prepare_dicom_images(input_data_folder, output_data_folder, exam_list_path):
    dcm_files = glob.glob(os.path.join(input_data_folder,"**","*.dcm"), recursive=True)
    os.makedirs(output_data_folder, exist_ok=True)
    saving_images.save_dicom_image_as_png(find_view(dcm_files,"L","CC"), 
                                          os.path.join(output_data_folder,"L_CC.png"))  
    saving_images.save_dicom_image_as_png(find_view(dcm_files,"R","CC"), 
                                          os.path.join(output_data_folder,"R_CC.png"))  
    saving_images.save_dicom_image_as_png(find_view(dcm_files,"L","MLO"), 
                                          os.path.join(output_data_folder,"L_MLO.png"))  
    saving_images.save_dicom_image_as_png(find_view(dcm_files,"R","MLO"), 
                                          os.path.join(output_data_folder,"R_MLO.png")) 
    exam_list = [{
        'horizontal_flip': 'NO',
        'L-CC': ['L_CC'],
        'R-CC': ['R_CC'],
        'L-MLO': ['L_MLO'],
        'R-MLO': ['R_MLO']
    }]
    pickling.pickle_to_file(exam_list_path, exam_list)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare DICOM images by identifying relevant views and saving as png')
    parser.add_argument('--input-data-folder', required=True)
    parser.add_argument('--output-data-folder', required=True)
    parser.add_argument('--exam-list-path', required=True)
    args = parser.parse_args()
    
    prepare_dicom_images(
        input_data_folder=args.input_data_folder, 
        exam_list_path=args.exam_list_path, 
        output_data_folder=args.output_data_folder
    )