import os
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
from sentence_transformers import SentenceTransformer
import pinecone

from transformers import GPT2TokenizerFast, ViTImageProcessor, VisionEncoderDecoderModel
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

model_raw = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
image_processor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
tokenizer       = GPT2TokenizerFast.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
def show_n_generate(path, greedy = True, model = model_raw):
    image = Image.open(path)
    pixel_values   = image_processor(image, return_tensors ="pt").pixel_values
    if greedy:
        generated_ids  = model.generate(pixel_values, max_new_tokens = 30)
    else:
        generated_ids  = model.generate(
            pixel_values,
            do_sample=True,
            max_new_tokens = 30,
            top_k=5)
    generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return(generated_text)

model = SentenceTransformer('all-MiniLM-L6-v2')

async def setup():
    global index
    pinecone.init(api_key="21e5c3ed-7192-45b3-8b7e-cc80e354a5f5", environment="us-west4-gcp-free")
    index = pinecone.Index(index_name="my-index")
    index.describe_index_stats()
    print("Setup Complete")
    return("OK")

global IS_SETUP, index
IS_SETUP = False

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
IMG_DIR = "search/sets/nuimages/samples"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=['GET', 'POST'])
async def index():
    global IS_SETUP
    if not IS_SETUP:
        await setup()
        IS_SETUP = True

    if request.method == 'POST':
       
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
       
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(request.form.get("file_name") + "." + file.filename.split(".")[-1])
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            return redirect(url_for('get_caption', filename=filename))
    return render_template("index.html")


@app.route("/captions/<filename>", methods=["GET", "POST"])
def get_caption(filename):
    caption = show_n_generate(os.path.join(app.config['UPLOAD_FOLDER'], filename), greedy=False)
    if request.method == 'POST':
        query_embedding = model.encode(caption)

        query_vector = [float(e) for e in query_embedding]
        res = index.query(vector=query_vector, top_k=5, include_values=True, include_metadata=True)
        ids = []
        paths = []
        res_captions = []

        for e in res['matches']:
            ids.append(e['id'])
            paths.append(e['metadata']["path"].split("/")[-1])
            res_captions.append(e['metadata']["sentence"])

        # paths contains filenames of images.
        # ids contains id in pinecone of similar matches.
        # res_captions contains actual captions in pinecone of similar matches.
        num_img = len(ids)

        return render_template('results.html', img_list=paths, id_list=ids, caption_list=res_captions, num_img=num_img)
        
    print(url_for('uploaded_file', filename=filename))
    return render_template("caption.html", caption=caption, image_src=url_for('uploaded_file', filename=filename))


@app.route('/results/<img_list>/<id_list>/<caption_list>/<num_img>', methods=["POST"])
def get_results(img_list, id_list, caption_list, num_img):
    return render_template("results.html", img_list=img_list, id_list=id_list, caption_list=caption_list, num_img=num_img)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/search/<filename>')
def searched_files(filename):
    return send_from_directory("search/sets/nuimages/samples",
                               filename)


if __name__ == "__main__":
    app.run(debug=True)
