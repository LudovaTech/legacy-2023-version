import json, sensor, pyb
#import datetime

counter_image = 0
JSON_PATH = '_annotations.coco.json'


def saveImageForAI(img, blob):

    global counter_image

    if blob is None:
        counter_image += 1
        IMAGE_NAME = "image" + str(counter_image) + ".jpg"
        img.save(f"{IMAGE_NAME}")
        return

    try:
        # Ouvrir le fichier texte en mode lecture (par défaut)
        with open(JSON_PATH, 'r') as fichier:
            data = json.load(fichier)
        # Le fichier se ferme automatiquement à la fin du bloc 'with'
    except:
        # le fichier n'existe pas, on initialise le json
        data = {
            "info": {
                "description": "orange ball",
                "version": "1.0",
                "year": 2023,
                "contributor": "remy",
                "date_created": "2023-10-09"
            },
            "categories": [
                {
                    "id": 1,
                    "name": "ball"
                }
            ],
            "images": [
            ],
            "annotations": [
            ]
        }

        # À ce stade, 'data' contient maintenant le contenu du fichier JSON sous forme de structure de données Python (dictionnaires, listes, chaînes, nombres, booléens, etc.).

    counter_image = len(data["images"])

    # sauvegarder l'image brute
    IMAGE_NAME = "image" + str(counter_image) + ".jpg"
    img.save(f"{IMAGE_NAME}")

    # mettre à jour le json
    counter_image += 1

    newImage = {
        "id": counter_image,  # L'ID de l'image (assurez-vous qu'il est unique)
        "height": img.height(),
        "width": img.width(),
        "file_name": IMAGE_NAME
    }

    # Ajouter la nouvelle image à la liste des images existantes
    data["images"].append(newImage)

    newAnnotation = {
        "id": counter_image,
        "image_id": counter_image,
        "category_id": 1,
        "bbox": [blob.x(), blob.y(), blob.w(), blob.h()]
    }
    data["annotations"].append(newAnnotation)

    # Enregistrer le JSON mis à jour dans le fichier
    with open(JSON_PATH, 'w') as fichier:
        json.dump(data, fichier)


offset_x = 152
offset_y = 120
Min = 26
Max = int(Min * 6.5)
threshold_ball = (0, 100, 38, 127, 0, 127)

# Camera sensor initialisation
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=800)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)

sensor.set_brightness(1)
sensor.set_saturation(-1)
sensor.set_contrast(-3)

while(True):

    img = sensor.snapshot()

    # Hide non-interesting areas of the image
    img.draw_circle(offset_x, offset_y, Min, fill = True, color = (0,0,0))
    img.draw_circle(offset_x, offset_y, int(Max*1.25), fill = False, color = (0,0,0), thickness = Max)

    maxRoundness = 0
    detected_blob = None

    # Checks every blob detected
    for blob in img.find_blobs([threshold_ball], pixels_threshold=2, merge=True):

        # Checks if the blob's parameters are within an established range
        if blob.roundness() > maxRoundness and blob.area() < 300 and blob.compactness() > 0:
            maxRoundness = blob.roundness()
            detected_blob = blob

    saveImageForAI(img, detected_blob)














