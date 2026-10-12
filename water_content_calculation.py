import os
import cv2
import numpy as np
import pandas as pd

# ==== Configuration parameters ====
folder = r"C:\Users\30869\Desktop\2"  # Image folder
save_xlsx = r"C:\Users\30869\Desktop\blue_white_ratio_final.xlsx"

# Define region radii
radius_values = [60, 120, 180, 240, 300]
start_angle, end_angle = 0, -90  # Quarter circle centered at the lower-left corner

# HSV thresholds for color ranges (confirmed parameters)
blue_lower = np.array([100, 50, 50])  # Lower blue threshold
blue_upper = np.array([130, 255, 255])  # Upper blue threshold

white_lower = np.array([0, 0, 200])  # Lower white threshold
white_upper = np.array([180, 30, 255])  # Upper white threshold

all_data = []

# ==== 1. Read each image and calculate the blue/(blue + white) ratio ====
print("Processing 16 images...")
print("Formula: blue area / (blue area + white area) * 100%")

for i in range(1, 17):  # 16 images
    fname = f"{i}.tif"
    img_path = os.path.join(folder, fname)
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)

    if img is None:
        print(f"Unable to read {fname}; skipping")
        continue

    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Create blue and white masks
    blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
    white_mask = cv2.inRange(hsv, white_lower, white_upper)

    h, w = img.shape[:2]
    center = (0, h)  # Center at the lower-left corner

    # Store results for each region
    region_results = {}
    region_details = {}  # Store detailed data for debugging

    # Calculate the small circular region (0-60)
    mask_small = np.zeros((h, w), np.uint8)
    cv2.ellipse(mask_small, center, (60, 60), 0, start_angle, end_angle, 255, -1)

    # Blue and white pixel counts in the small circular region
    blue_in_small = cv2.bitwise_and(blue_mask, blue_mask, mask=mask_small)
    white_in_small = cv2.bitwise_and(white_mask, white_mask, mask=mask_small)

    blue_pixels_small = np.count_nonzero(blue_in_small)
    white_pixels_small = np.count_nonzero(white_in_small)
    total_blue_white_small = blue_pixels_small + white_pixels_small

    # Calculate the blue/(blue + white) ratio
    if total_blue_white_small > 0:
        blue_white_ratio_small = (blue_pixels_small / total_blue_white_small) * 100
    else:
        blue_white_ratio_small = 0

    region_results['Circle_60'] = blue_white_ratio_small
    region_details['Circle_60'] = {
        'blue_pixels': blue_pixels_small,
        'white_pixels': white_pixels_small,
        'total_blue_white': total_blue_white_small
    }

    # Calculate the four annular regions
    ring_names = ['Ring_60_120', 'Ring_120_180', 'Ring_180_240', 'Ring_240_300']

    for j in range(len(radius_values) - 1):
        r_in, r_out = radius_values[j], radius_values[j + 1]

        # Create an annular mask
        mask_big = np.zeros((h, w), np.uint8)
        mask_small_ring = np.zeros((h, w), np.uint8)
        cv2.ellipse(mask_big, center, (r_out, r_out), 0, start_angle, end_angle, 255, -1)
        cv2.ellipse(mask_small_ring, center, (r_in, r_in), 0, start_angle, end_angle, 255, -1)

        ring_mask = cv2.subtract(mask_big, mask_small_ring)

        # Blue and white pixel counts in the annular region
        blue_in_ring = cv2.bitwise_and(blue_mask, blue_mask, mask=ring_mask)
        white_in_ring = cv2.bitwise_and(white_mask, white_mask, mask=ring_mask)

        blue_pixels_ring = np.count_nonzero(blue_in_ring)
        white_pixels_ring = np.count_nonzero(white_in_ring)
        total_blue_white_ring = blue_pixels_ring + white_pixels_ring

        # Calculate the blue/(blue + white) ratio
        if total_blue_white_ring > 0:
            blue_white_ratio_ring = (blue_pixels_ring / total_blue_white_ring) * 100
        else:
            blue_white_ratio_ring = 0

        region_results[ring_names[j]] = blue_white_ratio_ring
        region_details[ring_names[j]] = {
            'blue_pixels': blue_pixels_ring,
            'white_pixels': white_pixels_ring,
            'total_blue_white': total_blue_white_ring
        }

    # Calculate the large circular region (0-300) as a reference
    mask_large = np.zeros((h, w), np.uint8)
    cv2.ellipse(mask_large, center, (300, 300), 0, start_angle, end_angle, 255, -1)

    blue_in_large = cv2.bitwise_and(blue_mask, blue_mask, mask=mask_large)
    white_in_large = cv2.bitwise_and(white_mask, white_mask, mask=mask_large)

    blue_pixels_large = np.count_nonzero(blue_in_large)
    white_pixels_large = np.count_nonzero(white_in_large)
    total_blue_white_large = blue_pixels_large + white_pixels_large

    if total_blue_white_large > 0:
        blue_white_ratio_large = (blue_pixels_large / total_blue_white_large) * 100
    else:
        blue_white_ratio_large = 0

    region_results['Circle_300'] = blue_white_ratio_large
    region_details['Circle_300'] = {
        'blue_pixels': blue_pixels_large,
        'white_pixels': white_pixels_large,
        'total_blue_white': total_blue_white_large
    }

    # Store results
    result_row = {"File": fname}
    for region_name, ratio in region_results.items():
        result_row[f"{region_name}_blue_white_ratio"] = ratio

    # Add detailed data (optional, for debugging)
    for region_name, details in region_details.items():
        result_row[f"{region_name}_blue_pixels"] = details['blue_pixels']
        result_row[f"{region_name}_white_pixels"] = details['white_pixels']
        result_row[f"{region_name}_total_pixels"] = details['total_blue_white']

    all_data.append(result_row)

    print(f"Processing complete: {fname}")
    print(f"  Overall blue/(blue + white) ratio: {blue_white_ratio_large:.2f}% (blue:{blue_pixels_large}, white:{white_pixels_large})")

# ==== 2. Save results to Excel ====
df = pd.DataFrame(all_data)
df.to_excel(save_xlsx, index=False)

print(f"\nAll images processed. Results saved to: {save_xlsx}")

# ==== 3. Display summary statistics ====
print("\n" + "=" * 80)
print("Summary statistics for the blue/(blue + white) ratio")
print("=" * 80)

regions = ["Circle_60", "Ring_60_120", "Ring_120_180", "Ring_180_240", "Ring_240_300", "Circle_300"]

print(f"{'Region':<18} {'Mean (%)':<10} {'Std. dev.':<8} {'Min (%)':<10} {'Max (%)':<10}")
print("-" * 80)

for region in regions:
    col_name = f"{region}_blue_white_ratio"
    values = df[col_name]
    print(f"{region:<18} {values.mean():>9.2f}% {values.std():>7.2f} {values.min():>9.2f}% {values.max():>9.2f}%")

# ==== 4. Display detailed results for each image ====
print("\n" + "=" * 80)
print("Detailed results for each image (blue/(blue + white) percentage)")
print("=" * 80)

for index, row in df.iterrows():
    print(f"\n{row['File']}:")
    for region in regions:
        col_name = f"{region}_blue_white_ratio"
        blue_col = f"{region}_blue_pixels"
        white_col = f"{region}_white_pixels"
        print(f"  {region}: {row[col_name]:5.2f}% (blue:{row[blue_col]}, white:{row[white_col]})")

print(f"\n" + "=" * 80)
print("Analysis complete!")
print(f"Processed {len(df)} images in total")
print(f"Region radii used: {radius_values}")
print(f"Formula: blue area / (blue area + white area) * 100%")
print(f"Gray areas are excluded")
print("=" * 80)