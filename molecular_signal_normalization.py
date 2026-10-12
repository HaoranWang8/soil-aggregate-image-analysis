# -*- coding: utf-8 -*-
"""
Created on Fri Sep 19 21:47:28 2025

@author: 30869
"""
import cv2
import numpy as np
import os
import pandas as pd

# === Path settings ===
folder = r"C:\Users\30869\Desktop\1"     # Image folder
save_xlsx = r"C:\Users\30869\Desktop\result_with_norm.xlsx"

# ROI parameters
radius_values = [48, 96, 144, 192, 240]
start_angle, end_angle = 0, -90

# Store results for all images
all_data = []

# === Batch processing: images 1-64 ===
for i in range(1, 65):
    fname = f"{i}.tif"
    fpath = os.path.join(folder, fname)
    image = cv2.imread(fpath, cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"Warning: unable to read {fname}")
        continue

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    center = (0, h)  # Center at the lower-left corner

    # Calculate the four rings
    ring_means = []
    for j in range(len(radius_values) - 1):
        r_in, r_out = radius_values[j], radius_values[j + 1]
        big_mask  = np.zeros((h, w), np.uint8)
        small_mask = np.zeros((h, w), np.uint8)
        cv2.ellipse(big_mask,  center, (r_out, r_out), 0, start_angle, end_angle, 255, -1)
        cv2.ellipse(small_mask, center, (r_in, r_in),   0, start_angle, end_angle, 255, -1)
        ring_mask = cv2.subtract(big_mask, small_mask)
        ring_mean = np.mean(gray[ring_mask != 0])
        ring_means.append(ring_mean)

    # Small circle with radius 48
    mask_small = np.zeros((h, w), np.uint8)
    cv2.ellipse(mask_small, center, (48, 48), 0, start_angle, end_angle, 255, -1)
    mean_small = np.mean(gray[mask_small != 0])

    # Large circle with radius 240
    mask_large = np.zeros((h, w), np.uint8)
    cv2.ellipse(mask_large, center, (240, 240), 0, start_angle, end_angle, 255, -1)
    mean_large = np.mean(gray[mask_large != 0])

    # ===== Normalize by the mean intensity of the large circle with radius 240 =====
    ring_norm = [x / mean_large for x in ring_means]
    small_norm = mean_small / mean_large
    large_norm = mean_large / mean_large  # =1

    # Save results for this image (raw and normalized)
    data_row = {
        "File": fname,
        # Raw mean intensity
        "Ring_48_96":  ring_means[0],
        "Ring_96_144": ring_means[1],
        "Ring_144_192":ring_means[2],
        "Ring_192_240":ring_means[3],
        "Circle_48":   mean_small,
        "Circle_240":  mean_large,
        # Normalized intensity
        "Ring_48_96_norm":  ring_norm[0],
        "Ring_96_144_norm": ring_norm[1],
        "Ring_144_192_norm":ring_norm[2],
        "Ring_192_240_norm":ring_norm[3],
        "Circle_48_norm":   small_norm,
        "Circle_240_norm":  large_norm
    }
    all_data.append(data_row)

# === Write to Excel ===
df = pd.DataFrame(all_data)
df.to_excel(save_xlsx, index=False)
print(f"Processing complete. Results saved to {save_xlsx}")
