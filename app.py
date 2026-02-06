import io
import base64
import torch
import clip
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)

# Setup Device
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
model.eval()

# 1. Cleaned Object List (Removed duplicates and added missing items)
OBJECT_CLASSES = [
    # --- ANIMALS (Mammals) ---
    "cow", "lion", "tiger", "zebra", "elephant", "giraffe", "monkey", "gorilla", "panda", "bear", 
    "polar bear", "koala", "kangaroo", "llama", "hippo", "rhino", "camel", "deer", "fox", "wolf", 
    "dog", "cat", "rabbit", "hamster", "mouse", "rat", "pig", "sheep", "goat", "horse", "donkey","hedgehog","mouse","goose",
    "hippopotamus","squirrel"
    
    # --- ANIMALS (Birds/Reptiles/Insects) ---
    "bird", "owl", "duck", "chicken", "chick", "penguin", "parrot", "eagle", "swan", "flamingo",
    "snake", "turtle", "crocodile", "frog", "dinosaur", "dragon" , "butterfly", "spider", 
    "ladybug", "ant", "snail", "fish", "shark", "whale", "dolphin", "octopus", "crab",
    
    # --- PEOPLE & FANTASY ---
    "child", "baby", "boy", "girl", "man", "woman", "robot", "monster", "alien", "ghost", 
    "superhero", "wizard", "fairy", "clown", "astronaut",
    
    # --- TRANSPORT & VEHICLES ---
    "car", "truck", "bus", "train", "airplane", "helicopter", "rocket", "boat", "ship", "submarine",
    "bicycle", "motorcycle", "scooter", "tractor", "ambulance", "fire truck", "police car",
    
    # --- TOYS & HOUSEHOLD ---
    "toy", "doll", "teddy bear", "ball", "balloon", "kite", "piano", "guitar", "drum", "book", 
    "pencil", "clock", "lamp", "chair", "table", "bed", "phone", "computer", "camera", "television",
    "umbrella", "key", "gift box", "hat", "shoes", "glasses",
    
    # --- NATURE & FOOD ---
    "tree", "flower", "grass", "mushroom", "sun", "moon", "star", "cloud", "rainbow", "mountain", 
    "house", "castle", "bridge", "apple", "banana", "orange", "strawberry", "cake", "ice cream", 
    "pizza", "burger", "carrot", "corn"
]

COLOR_CLASSES = [
    "red", "blue", "green", "yellow", "orange",
    "purple", "pink", "brown", "black", "white",  
 
]

# 2. PRE-COMPUTE TEXT FEATURES (Runs once when server starts)
with torch.no_grad():
    obj_tokens = clip.tokenize([f"a cartoon {c}" for c in OBJECT_CLASSES]).to(device)
    obj_text_features = model.encode_text(obj_tokens)
    obj_text_features /= obj_text_features.norm(dim=-1, keepdim=True)

    color_tokens = clip.tokenize([f"a {c} colored object" for c in COLOR_CLASSES]).to(device)
    color_text_features = model.encode_text(color_tokens)
    color_text_features /= color_text_features.norm(dim=-1, keepdim=True)

@app.route("/classify", methods=["POST"])
def classify():
    try:
        data = request.get_json()
        image_str = data["image"]
        if image_str.startswith("data:"):
            image_str = image_str.split(",", 1)[1]

        img_bytes = base64.b64decode(image_str)
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        
        w, h = image.size
        cell_w, cell_h = w / 3, h / 3
        padding = 8
        
        cells_tensors = []
        metadata = []

        # Step 1: Crop all cells and prepare a batch
        for r in range(3):
            for c in range(3):
                idx = r * 3 + c
                left, top = int(c * cell_w), int(r * cell_h)
                right, bottom = int((c + 1) * cell_w), int((r + 1) * cell_h)
                
                cell = image.crop((left + padding, top + padding, right - padding, bottom - padding))
                cells_tensors.append(preprocess(cell))
                metadata.append({"grid_position": idx, "bbox": [left, top, right, bottom]})

        # Step 2: Process the entire batch at once (The Fast Part)
        image_input = torch.stack(cells_tensors).to(device)
        
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)

            # Batch similarity for Objects
            obj_similarity = (100.0 * image_features @ obj_text_features.T).softmax(dim=-1)
            obj_confs, obj_indices = obj_similarity.topk(1)

            # Batch similarity for Colors
            color_similarity = (100.0 * image_features @ color_text_features.T).softmax(dim=-1)
            _, color_indices = color_similarity.topk(1)

        # Step 3: Format Results
        results = []
        for i in range(len(metadata)):
            obj_name = OBJECT_CLASSES[obj_indices[i]]
            color_name = COLOR_CLASSES[color_indices[i]]
            
            # Keep your custom fix if needed
            if obj_name == "kangaroo" and color_name == "red":
                obj_name = "llama"

            results.append({
                "grid_position": metadata[i]["grid_position"],
                "object_name": f"{color_name} {obj_name}",
                "detected_color": color_name,
                "confidence": round(obj_confs[i].item(), 3),
                "bbox": metadata[i]["bbox"]
            })

        return jsonify({"grid_size": "3x3", "detected_objects": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Use threaded=True or a production WSGI server for even better performance
    app.run(host="0.0.0.0", port=5000, threaded=True)