import os
import glob
import argparse
import tqdm
import pydicom
import numpy as np
from PIL import Image

from pydicomutils.IODs.SCImage import SCImage

import src.utilities.pickling as pickling
import src.data_loading.loading as loading
from src.constants import VIEWS

def find_view(dcm_files, laterality, view):
    for dcm_file in dcm_files:
        ds = pydicom.read_file(dcm_file)
        if ds.ImageLaterality == laterality and ds.ViewPosition == view:
            return dcm_file
    raise RuntimeError()

def convert_output_results(input_data_folder, heatmaps_path, 
                           data_path, output_data_folder):
    exam_list = pickling.unpickle_from_file(data_path)
    os.makedirs(os.path.dirname(output_data_folder), exist_ok=True)
    dcm_files = glob.glob(os.path.join(input_data_folder,"**","*.dcm"), recursive=True)
    image_extension = ".png"
    for datum in tqdm.tqdm(exam_list):
        loaded_heatmaps_dict = {view: [] for view in VIEWS.LIST}
        for view in VIEWS.LIST:
            for short_file_path in datum[view]:
                loaded_heatmaps = loading.load_heatmaps(
                    benign_heatmap_path=os.path.join(heatmaps_path, "heatmap_benign",
                                                     short_file_path + image_extension),
                    malignant_heatmap_path=os.path.join(heatmaps_path, "heatmap_malignant",
                                                        short_file_path + image_extension),
                    view=view,
                    horizontal_flip=datum["horizontal_flip"],
                )
                loaded_heatmaps_dict[view].append(loaded_heatmaps)
                loaded_heatmaps = np.stack([loaded_heatmaps[:,:,1:2], 
                                            loaded_heatmaps[:,:,0:1], 
                                            np.zeros(loaded_heatmaps[:,:,1:2].shape)], 
                                            axis=2)[:,:,:,0].astype(np.uint8)

                laterality = view.split("-")[0]
                projection_view = view.split("-")[1]
                dcm_file = find_view(dcm_files, laterality, projection_view)
                ds = pydicom.read_file(dcm_file)
                pixel_array = ds.pixel_array
                pixel_array = (pixel_array - np.min(pixel_array)) / float(np.max(pixel_array) - np.min(pixel_array)) * 255
                pixel_array = np.expand_dims(pixel_array.astype(np.uint8), axis=2)
                pixel_array = np.stack([pixel_array, pixel_array, pixel_array], axis=2)[:,:,:,0]
                coords = datum["window_location"][view][0]
                if laterality == "R":
                    loaded_heatmaps = np.fliplr(loaded_heatmaps)
                sub_pixel_array = pixel_array[coords[0]:coords[1],coords[2]:coords[3],0:3]
                bg = Image.fromarray(sub_pixel_array)
                fg = Image.fromarray(loaded_heatmaps)
                blended = Image.blend(bg, fg, 0.25)
                pixel_array[coords[0]:coords[1],coords[2]:coords[3],0:3] = np.asarray(blended)
                sc_image = SCImage()
                sc_image.create_empty_iod()
                sc_image.initiate()
                sc_image.set_dicom_attribute("PatientName", ds.PatientName)
                sc_image.set_dicom_attribute("PatientID", ds.PatientID)
                sc_image.set_dicom_attribute("AccessionNumber", ds.AccessionNumber)
                sc_image.set_dicom_attribute("StudyID", ds.StudyID)
                sc_image.set_dicom_attribute("StudyInstanceUID", ds.StudyInstanceUID)
                sc_image.set_dicom_attribute("StudyDate", ds.StudyDate if "StudyDate" in ds else "")
                sc_image.set_dicom_attribute("StudyTime", ds.StudyTime if "StudyTime" in ds else "")
                sc_image.set_dicom_attribute("StudyDescription", ds.StudyTime if "StudyDescription" in ds else "")
                sc_image.set_dicom_attribute("SeriesDescription", f"Original {view} + heatmap")
                # sc_image.add_pixel_data(loaded_heatmaps)
                sc_image.add_pixel_data(pixel_array)
                output_file = os.path.join(output_data_folder, "SC_" + view + ".dcm")
                sc_image.write_to_file(output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert results to DICOM')
    parser.add_argument('--input-data-folder', required=True)
    parser.add_argument('--heatmaps-path', required=True)
    parser.add_argument('--data-path', required=True)
    parser.add_argument('--output-data-folder', required=True)
    args = parser.parse_args()
    
    convert_output_results(
        input_data_folder=args.input_data_folder, 
        heatmaps_path=args.heatmaps_path, 
        data_path=args.data_path, 
        output_data_folder=args.output_data_folder
    )