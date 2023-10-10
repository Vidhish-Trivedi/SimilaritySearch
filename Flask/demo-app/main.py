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

# C:\Users\HP\Desktop\WSL\Data\data\sets\nuimages\samples
# UPLOAD_FOLDER = '/path/to/the/uploads'
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
        # print(request.form.get("file_name"))
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            filename = secure_filename(request.form.get("file_name") + "." + file.filename.split(".")[-1])
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # return redirect(url_for('uploaded_file', filename=filename))
            return redirect(url_for('get_caption', filename=filename))
    return render_template("index.html")


@app.route("/captions/<filename>", methods=["GET", "POST"])
def get_caption(filename):
    caption = show_n_generate(os.path.join(app.config['UPLOAD_FOLDER'], filename), greedy=False)
    if request.method == 'POST':
        print("ok post")
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

        # img_path_list = []
        # ids contains ids of closest matches.
        # for _ in range(0, 5):
        #     print(ids[_], paths[_], res_captions[_])
            # 5194 n013-2018-08-17-12-00-39+0800__CAM_FRONT__1534479305912407.jpg a car with a lot of luggage parked on the curb

            # img_data_path = IMG_DIR
            # img_data_path = ""
            # if "FRONT" in paths[_]:
            #     if "LEFT" in paths[_]:
            #         img_data_path += "CAM_FRONT_LEFT"
            #     elif "RIGHT" in paths[_]:
            #         img_data_path += "CAM_FRONT_RIGHT"
            #     else:
            #         img_data_path += "CAM_FRONT"
            
            # elif "BACK" in paths[_]:
            #     if "LEFT" in paths[_]:
            #         img_data_path += "CAM_BACK_LEFT"
            #     elif "RIGHT" in paths[_]:
            #         img_data_path += "CAM_BACK_RIGHT"
            #     else:
            #         img_data_path += "CAM_BACK"
            
            # img_data_path += "/" + paths[_]
            # img_path_list.append(img_data_path)

        num_img = len(ids)
        # print("=============> ", num_img)

        # resp_list = []
        # for p in img_path_list:
        #     resp_list.append(url_for('searched_files', img_path=p))
        
        # print("=============> ", resp_list[0])

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
    # print("/".join(img_path.split("/")[:-1]))
    # print(img_path.split("/")[-1])
    # return send_from_directory("/".join(img_path.split("/")[:-1]), img_path.split("/")[-1])


if __name__ == "__main__":
    app.run(debug=True)
