import cv2
import numpy as np
import os
import img2pdf

paper_width, paper_height = 1063, 1375

# create a blank white image
clue_image = np.zeros((paper_height, paper_width, 3), np.uint8)
clue_image.fill(255)

ans_image = np.zeros((paper_height, paper_width, 3), np.uint8)
ans_image.fill(255)

card_width, card_height = 190, 315
text_width, text_height = 190, 50
image_width, image_height = 190, card_height - text_height
ans_box_width, ans_box_height = 95, 25
card_padding = 19
image_padding = 10

font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 0.5
fontThickness = 1
linetype = cv2.LINE_AA

def get_maps(paper_width, paper_height, card_width, card_height, padding):
    coord_map = {}
    mirror_map = {}
    for i in range(padding, paper_height, card_height + padding):
        mini_coord_map = {}
        mini_mirror_map = {}
        for j in range(padding, paper_width, card_width + padding):
            if i + card_height > paper_height or j + card_width > paper_width:
                continue
            mini_coord_map[len(mini_coord_map) + len(coord_map)] = (j, i)
        coord_map = {**coord_map, **mini_coord_map}
        for index, (card_index, cords) in enumerate(mini_coord_map.items()):
            mini_mirror_map[card_index] = len(coord_map) - index - 1
        mirror_map = {**mirror_map, **mini_mirror_map}
    return coord_map, mirror_map

def draw_borders(img, co_ord_map):
    for index, (card_index, cords) in enumerate(co_ord_map.items()):
        i, j = cords
        # draw a card
        cv2.rectangle(img, (i, j), (i + card_width, j + card_height), (0, 0, 0), 1)
        # draw an image box
        cv2.rectangle(img, (i + image_padding, j + image_padding), (i + image_width - image_padding, j + image_height), (0, 0, 0), 1)
        # draw a text box
        cv2.rectangle(img, (i, j + image_height), (i + text_width, j + card_height), (0, 0, 0), 1)
        # draw an answer box on the ans page on top of text box
        cv2.rectangle(img, (i +image_padding+(image_width//4), j + image_height - ans_box_height), (i + image_width - image_padding - (image_width//4), j + image_height), (0, 0, 0), 1)
    return img

def get_images():
    images = {}
    for image_name in os.listdir('images_1'):
        image = cv2.imread('images_1\\' + image_name)
        image = cv2.resize(image, (image_width-2*image_padding, image_height-2*image_padding), interpolation=cv2.INTER_AREA)
        images[image_name] = image
    return images

def create_clue_and_ans_pages(clue_img, ans_img, images, clues, answers, card_cord_map, mirror_map):
    for index, image in enumerate(images):
        # create clue page
        x, y = card_cord_map[index]
        clue_img[y+image_padding:y+image_height-image_padding, x+image_padding:x+image_width-image_padding] = image
        text = clues[index]
        textsize = cv2.getTextSize(text, font, fontScale, fontThickness)[0]
        text_x = x + (text_width - textsize[0]) // 2
        text_y = y + image_height + (text_height + textsize[1]) // 2
        cv2.putText(clue_img, text, (text_x, text_y), font, fontScale, (0, 0, 0), fontThickness, linetype)

        # create ans page
        mirror_x, mirror_y = card_cord_map[mirror_map[index]]
        ans_img[mirror_y+image_padding:mirror_y+image_height-image_padding, mirror_x+image_padding:mirror_x+image_width-image_padding] = image
        text = str(answers[index])
        textsize = cv2.getTextSize(text, font, fontScale, fontThickness)[0]
        text_x = mirror_x + (text_width - textsize[0]) // 2
        text_y = mirror_y + image_height + (text_height + textsize[1]) // 2
        cv2.putText(ans_img, text, (text_x, text_y), font, fontScale, (0, 0, 0), fontThickness, linetype)
    return clue_img, ans_img

def create_pdf_from_img_objs(img_objs, pdf_name):
    image_names = []
    for index, img_obj in enumerate(img_objs):
        image_name = f'image-{index}.png'
        cv2.imwrite(image_name, img_obj)
        image_names.append(image_name)

    with open(pdf_name, "wb") as f:
        f.write(img2pdf.convert(*image_names)) # type: ignore

co_ord_map, mirror_map = get_maps(paper_width, paper_height, card_width, card_height, card_padding)
print(co_ord_map)
print(mirror_map)

clue_image = draw_borders(clue_image, co_ord_map)
ans_image = draw_borders(ans_image, co_ord_map)

images = get_images()

clues = os.listdir('images_1')
answers = range(0, len(clues))

clue_image, ans_image = create_clue_and_ans_pages(clue_image, ans_image, images.values(), clues, answers, co_ord_map, mirror_map)

cv2.imshow('clue', clue_image)
cv2.imshow('ans', ans_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# create_pdf_from_img_objs([clue_image, ans_image], 'result.pdf')