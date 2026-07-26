from PIL import Image

def image_to_grid(image_path, color_map):
    img = Image.open(image_path).convert("RGB")
    cell_size = img.width // 10  # 16 for a 160x160 image, 10x10 grid

    grid = []
    for row in range(10):
        grid_row = []
        for col in range(10):
            x = col * cell_size + cell_size // 2
            y = row * cell_size + cell_size // 2
            pixel_color = img.getpixel((x, y))
            grid_row.append(color_map[pixel_color])
        grid.append(grid_row)
    return grid

# Example usage
color_map = {
    (151, 98, 23): 1,
    (0, 0, 0): 0,
    (91, 110, 225): 2,
    (16, 134, 14): 3,
    (118, 39, 146): 4,

}

for i in range(1, 21):
    grid = image_to_grid(f"level-{i}.png", color_map)
    print(f"'{i}': {'{'}'timers': [], ")
    print(f"'countdown_tiles': [], ")
    print("'grid': [")
    for row in grid:
        print(f"{row}, ")
    print(']},')