from flask import Flask, render_template, request,jsonify
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from nltk.tokenize.treebank import TreebankWordDetokenizer
from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import CountVectorizer
import re
from flask_cors import CORS,cross_origin
import os
from wordcloud import WordCloud
from PIL import Image
import pickle
import numpy
app= Flask(__name__)

@app.route('/',methods=['GET'])
@cross_origin()
def homePage():
	return render_template("index.html")


@app.route('/count',methods=['POST','GET'])
@cross_origin()
def counts():
    if request.method == 'POST':
        try:
            list1=[]
            productLink = request.form['content']
            counts.link = productLink
            prodRes = requests.get(productLink)
            prod_html = bs(prodRes.text, "html.parser")
            try:
                s = prod_html.find_all('div', {"class": "col JOpGWq"})[0].find_all('a', {"class": ""})[-1].get("href")
            except:
                s = ""
            if (s == ""):
                return render_template('noreviews.html')
                #print("No reviews yet")
            else:
                ans = "https://www.flipkart.com" + s
                sec = requests.get(ans)
                prod_sec = bs(sec.text, "html.parser")
                try:
                    k = int(prod_sec.find_all('div', {"class": "_2MImiq _1Qnn1K"})[0].find_all('span', {"class": ""})[0].text.split()[-1])
                    if(k>100):
                        k=100
                    else:
                        k=k
                except:
                    k=int("1")
                for z in range(1, k + 1):
                    ans1 = "https://www.flipkart.com" + s + "&page=" + str(z)
                    sec = requests.get(ans1)
                    prod_sec = bs(sec.text, "html.parser")
                    x = prod_sec.find_all("div", {"class": "_27M-vq"})
                    for i in x:
                        try:
                            comtag = i.div.div.find_all('div', {'class': ''})
                            custComment = comtag[0].div.text
                        except:
                            custComment = 'No Customer Comment'
                        list1.append(custComment)
            stop_words = set(stopwords.words('english'))
            ps = PorterStemmer()
            detokenizer = TreebankWordDetokenizer()
            resText = []
            try:
                for j in list1:
                    sentences = sent_tokenize(j)
                    for sentence in sentences:
                        sentence = sentence.lower()
                        words = word_tokenize(sentence)
                        stopped_words = [k for k in words if not k in stop_words]
                        stem_words = [ps.stem(word) for word in stopped_words]
                        new_sentence = detokenizer.detokenize(stem_words)
                    resText.append(new_sentence)
            except Exception as e:
                return e
            features = []
            for i in range(len(resText)):
            #for i in range(4):
                # remove all special characters
                feature = re.sub(r'\W', ' ', str(resText[i]))
                # remove all single characters
                feature = re.sub(r'\s+[a-zA-Z]\s+', ' ', feature)
                # Substituting multiple spaces with single space
                feature = re.sub(r'\s+', ' ', feature, flags=re.I)
                features.append(feature)
            counts.lists=features
            file1='vectorizer.pickle'
            file2='classification.model'
            loaded_vectorizer = pickle.load(open(file1,'rb'))
            loaded_model = pickle.load(open(file2,'rb'))
            preds=loaded_model.predict(loaded_vectorizer.transform(features[:]))
            l=list(preds)
            #l=[1,-1]
            positive=0
            negative=0
            for i in l:
                if(i==1):
                    positive+=1
                else:
                    negative+=1
            return render_template("counts.html",positive=positive,negative=negative)
        except Exception as e:
            return render_template('error.html')
    else:
        return render_template('index.html')


@app.route('/review',methods=['POST','GET'])
@cross_origin()
def index():
    if request.method == 'GET':
        try:
            reviews = []
            counts()
            productLink = counts.link
            prodRes = requests.get(productLink)
            prod_html = bs(prodRes.text, "html.parser")
            j=0
            try:
                prod_name = prod_html.find_all('span', {"class": "B_NuCI"})[0].text
            except:
                prod_name = "No product name"

            try:
                whole_rating = prod_html.find_all('div', {'class': "_2d4LTz"})[0].text
            except:
                whole_rating = "No ratings yet"

            try:
                price = prod_html.find_all('div', {'class': '_30jeq3'})[0].text
            except:
                price = "Zero"
            try:
                s = prod_html.find_all('div', {"class": "col JOpGWq"})[0].find_all('a', {"class": ""})[-1].get("href")
            except:
                s = ""
            if (s == ""):
                print("No reviews yet")
            else:
                ans = "https://www.flipkart.com" + s
                sec = requests.get(ans)
                prod_sec = bs(sec.text, "html.parser")
                try:
                    k = int(prod_sec.find_all('div', {"class": "_2MImiq _1Qnn1K"})[0].find_all('span', {"class": ""})[
                                0].text.split()[-1])
                    if(k>8):
                        k=8
                    else:
                        k=k

                except:
                    k = 1
                for z in range(1, k + 1):
                    ans1 = "https://www.flipkart.com" + s + "&page=" + str(z)
                    sec = requests.get(ans1)
                    prod_sec = bs(sec.text, "html.parser")
                    x = prod_sec.find_all("div", {"class": "_27M-vq"})
                    for i in x:
                        j += 1
                        try:
                            rating = i.div.div.div.div.text
                        except:
                            rating = 'No Rating'
                        try:
                            name = i.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text

                        except:
                            name = 'Anonymous'
                        try:
                            commentHead = i.div.div.div.p.text
                        except:
                            commentHead = 'No Comment Heading'
                        try:
                            comtag = i.div.div.find_all('div', {'class': ''})
                            custComment = comtag[0].div.text
                        except:
                            custComment = 'No Customer Comment'
                        mydict = {"i": j, "Product Name": prod_name, "Product Price": price,
                                          "Overall Rating": whole_rating,  "Customer Name": name, "Customer Rating": rating, "CommentHead": commentHead, "Comment": custComment}
                        reviews.append(mydict)
                return render_template('results.html',reviews=reviews)
        except:
            return render_template('error.html')
    else:
        return render_template('index.html')


@app.route('/showcloud',methods=['POST','GET'])
@cross_origin()
def show_wordcloud():
    if(request.method=="GET"):
	n=np.random.randint(500)
        counts()
        list1=counts.lists
        all = " ".join(i for i in list1)
        wc = WordCloud().generate(all)
	wc.to_file("static/wordcloud"+str(n)+".png")
        #filename=Image.open("static/wordcloud.png")
        #filename.show()
        return render_template('show.html',n1=str(n))
if __name__ == "__main__":
    app.run(port=8000,debug=True)
