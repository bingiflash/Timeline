import cv2
import numpy as np
import os
import img2pdf
import json

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
fontScale = 0.37
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
            mini_coord_map[len(mini_coord_map) + len(coord_map)] = {"card_coords":((j, i), (j + card_width, i + card_height))}
        coord_map = {**coord_map, **mini_coord_map}
        for index, (card_index, cords) in enumerate(mini_coord_map.items()):
            mini_mirror_map[card_index] = len(coord_map) - index - 1
        mirror_map = {**mirror_map, **mini_mirror_map}
    return coord_map, mirror_map

def draw_borders(img, co_ord_map):
    co_ord_map_copy = co_ord_map.copy()
    for index, (card_index, cords) in enumerate(co_ord_map.items()):
        (card_x1, card_y1), (card_x2, card_y2) = cords['card_coords']
        # draw a card
        cv2.rectangle(img, (card_x1, card_y1), (card_x2, card_y2), (0, 0, 0), 1)
        # draw an image box
        co_ord_map_copy[card_index]['image_coords'] = ((card_x1 + image_padding, card_y1 + image_padding), (card_x1 + image_width - image_padding, card_y1 + image_height))
        (image_x1, image_y1), (image_x2, image_y2) = co_ord_map_copy[card_index]['image_coords']
        cv2.rectangle(img, (image_x1, image_y1), (image_x2, image_y2), (0, 0, 0), 1)
        # draw a text box
        co_ord_map_copy[card_index]['text_coords'] = ((card_x1, card_y1 + image_height), (card_x1 + text_width, card_y1 + card_height))
        (text_x1, text_y1), (text_x2, text_y2) = co_ord_map_copy[card_index]['text_coords']
        cv2.rectangle(img, (text_x1, text_y1), (text_x2, text_y2), (0, 0, 0), 1)
        # get answer box coordinates, we'll draw it later
        co_ord_map_copy[card_index]['ans_box_coords'] = ((card_x1 + image_padding + (image_width//6), card_y1 + image_height - ans_box_height), (card_x1 + image_width - image_padding - (image_width//6), card_y1 + image_height))
    return img, co_ord_map_copy

def get_images(size):
    images = {}
    width, height = size
    for image_name in os.listdir('images_1'):
        image = cv2.imread('images_1\\' + image_name)
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
        images[image_name] = image
    return images

def create_clue_and_ans_pages(clue_img, ans_img, images, clues, answers, card_cord_map, mirror_map):
    for index, image in enumerate(images):
        # create clue page
        # x, y = card_cord_map[index]
        (image_x1, image_y1), (image_x2, image_y2) = card_cord_map[index]['image_coords']
        clue_img[image_y1:image_y2, image_x1:image_x2] = image
        # clue_img[y+image_padding:y+image_height-image_padding, x+image_padding:x+image_width-image_padding] = image
        text = clues[index]
        (text_x1, text_y1), (text_x2, text_y2) = card_cord_map[index]['text_coords']
        textsize = cv2.getTextSize(text, font, fontScale, fontThickness)[0]
        text_x = text_x1 + (text_width - textsize[0]) // 2
        text_y = text_y1 + (text_height + textsize[1]) // 2
        cv2.putText(clue_img, text, (text_x, text_y), font, fontScale, (0, 0, 0), fontThickness, linetype)
        
        # create ans page
        # mirror_x, mirror_y = card_cord_map[mirror_map[index]]
        (mirror_image_x1, mirror_image_y1), (mirror_image_x2, mirror_image_y2) = card_cord_map[mirror_map[index]]['image_coords']
        print(mirror_image_x1, mirror_image_y1, mirror_image_x2, mirror_image_y2)
        ans_img[mirror_image_y1:mirror_image_y2, mirror_image_x1:mirror_image_x2] = image
        # ans_img[mirror_y+image_padding:mirror_y+image_height-image_padding, mirror_x+image_padding:mirror_x+image_width-image_padding] = image
        text = clues[index]
        (mirror_text_x1, mirror_text_y1), (mirror_text_x2, mirror_text_y2) = card_cord_map[mirror_map[index]]['text_coords']
        textsize = cv2.getTextSize(text, font, fontScale, fontThickness)[0]
        text_x = mirror_text_x1 + (text_width - textsize[0]) // 2
        text_y = mirror_text_y1 + (text_height + textsize[1]) // 2
        cv2.putText(ans_img, text, (text_x, text_y), font, fontScale, (0, 0, 0), fontThickness, linetype)

        (ans_box_x1, ans_box_y1), (ans_box_x2, ans_box_y2) = card_cord_map[mirror_map[index]]['ans_box_coords']
        cv2.rectangle(ans_img, (ans_box_x1, ans_box_y1), (ans_box_x2, ans_box_y2), (0, 0, 0), 1)
        # fill answer box with white
        ans_img[ans_box_y1+1:ans_box_y2, ans_box_x1+1:ans_box_x2] = (255, 255, 255)

        ans_text = str(answers[index])
        textsize = cv2.getTextSize(ans_text, font, fontScale, fontThickness)[0]
        text_x = ans_box_x1 + (ans_box_width - textsize[0]) // 2
        text_y = ans_box_y1 + (ans_box_height + textsize[1]) // 2
        cv2.putText(ans_img, ans_text, (text_x, text_y), font, fontScale, (0, 0, 0), fontThickness, linetype)

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

clue_image, co_ord_map = draw_borders(clue_image, co_ord_map)
ans_image, _ = draw_borders(ans_image, co_ord_map)

(image_x1, image_y1), (image_x2, image_y2) = co_ord_map[0]['image_coords']
image_width = image_x2 - image_x1
image_height = image_y2 - image_y1

images = get_images((image_width, image_height))
manifest = json.load(open('manifest.json','r'))

clues = []
answers = []
for image_name in images.keys():
    for card in manifest['cards']:
        if card['file'] == image_name:
            clues.append(card['clue'])
            answers.append(card['answer'])

clue_image, ans_image = create_clue_and_ans_pages(clue_image, ans_image, images.values(), clues, answers, co_ord_map, mirror_map)

# cv2.imshow('clue', clue_image)
# cv2.imshow('ans', ans_image)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

create_pdf_from_img_objs([clue_image, ans_image], 'result.pdf')