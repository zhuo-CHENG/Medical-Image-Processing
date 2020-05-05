"""
2D DICOM series to NIFTI file
"""

import sys, os
import numpy as np
import SimpleITK as sitk
import argparse


def dcm_to_nii(img_path, img_name):

    # read header
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(img_path)
    reader.SetFileNames(dicom_names)
    header = reader.Execute()

    # set direction
    header.SetDirection(header.GetDirection())
    origin = list(header.GetOrigin())
    header.SetOrigin(tuple(origin))

    img_data = sitk.GetArrayFromImage(header)
    img_save = sitk.GetImageFromArray(img_data)
    
    # save nii image
    save_path = os.path.join(save_folder, img_name) +'.nii.gz'
    img_save.CopyInformation(header)
    writer = sitk.ImageFileWriter()
    writer.SetFileName(save_path)
    writer.Execute(img_save)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="DICOM to NIFTI")

    parser.add_argument(
        "-d_f",
        "--dcm_folder",
        default=None,
        type=str,
        help="The path of DICOM image folder",
    )

    parser.add_argument(
        "-n_f",
        "--nii_folder",
        default=None,
        type=str,
        help="The path of NIFTI image folder",
    )

    args = parser.parse_args()
    img_folder = args.dcm_folder
    save_folder = args.nii_folder
    if not os.path.exists(save_folder): os.makedirs(save_folder)

    # Get the the path list of files
    img_paths = [os.path.join(img_folder, o) for o in os.listdir(img_folder) 
                        if os.path.isdir(os.path.join(img_folder,o))]

    # Process CT images
    for img_path in img_paths:

        img_name = os.path.basename(img_path)
        img_name = img_name.split('.')[0]
        print("Processing: {}".format(img_name))

        dcm_to_nii(img_path, img_name)
