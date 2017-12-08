from flask import *
from flask import request, jsonify
from clean import *
from pandas_datareader.data import Options
from flask import Flask
from flask import Markup
from bunch_get import *
import markdown
import io
import base64
import matplotlib.pyplot as plt


def get_one_ticker(one_ticker_name):
    option_data = Options(one_ticker_name,data_source='yahoo').get_all_data()
    option_data.reset_index(inplace=True)
    option_data.drop(['IsNonstandard','Underlying','Symbol','JSON'], axis=1, inplace=True)
    return option_data


app=Flask(__name__)
@app.route('/')
def hello():
    return redirect(url_for('index'))

@app.route('/index',methods=['GET'])
def index():
  content = """
Option Data Web Gleaner API v1
=======

Team
----  
*Minglu Sun, MS. Business Analytics, msun40@fordham.edu*   
*Ye Wang, MS. Computer Science, ywang0811@gmail.edu*  
*Yiting Cai, MS. Business Analytics, ycai47@foreham.edu* 
"""
  content = Markup(markdown.markdown(content))
  return render_template('index.html', **locals())

@app.route('/api/v1/resources', methods=['GET'])
def api_id():
    if ('id' in request.args) and ('european' not in request.args):
        name = request.args['id']
        df = get_one_ticker(request.args['id'])
        rr = zip([df.to_html(classes='df')], [name])
        return render_template('view_total.html', rr=rr)

    if ('id' in request.args) and ('european' in request.args):
        if request.args['european'].lower()=='true':
            name=request.args['id']
            df=get_one_ticker(request.args['id'])
            df=clean(df)
            df.drop('index',inplace=True,axis=1)
            rr = zip([df.to_html(classes='df')],[name])
            return render_template('view.html',rr=rr)
    else:
        return "Error: No id field provided. Please specify an id."

@app.route('/api/v1/random',methods=['GET'])
def random():
    if ('k' in request.args) and ('european' in request.args):
        if request.args['european'].lower() == 'true':
            k = request.args['k']
            r = random_total_tickers(k,True)
            tbl_list = r[1]
            names = r[0]
            html_tbl_list = [i.to_html(classes='df') for i in tbl_list]
            rr = zip(html_tbl_list, names)
            return render_template('view.html', rr=rr)

    if 'k' in request.args:
        k = request.args['k']
        r = random_total_tickers(k)
        tbl_list = r[1]
        names = r[0]
        html_tbl_list = [i.to_html(classes='df') for i in tbl_list]
        rr = zip(html_tbl_list, names)
        return render_template('view_total.html', rr=rr)

@app.route('/api/v1/european/CSV/<ticker>')
def eu_download(ticker):
    csv=clean(get_one_ticker(ticker)).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                     "attachment; filename=ticker.csv"})

@app.route('/api/v1/raw/CSV/<ticker>')
def raw_download(ticker):
    csv=get_one_ticker(ticker).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                     "attachment; filename=ticker.csv"})

@app.route('/api/v1/industry',methods=['GET'])
def industry():
    if ('ind' in request.args) and ('k' in request.args) and ('european' in request.args):
        if request.args['european'].lower() == 'true':
            industry_type=request.args['ind']
            k=request.args['k']
            r=industry_tickers(industry_type,k,True)
            tbl_list = r[1]
            names = r[0]
            html_tbl_list = [i.to_html(classes='df') for i in tbl_list]
            rr = zip(html_tbl_list, names)
            return render_template('industry.html', rr=rr,type='euro',industry_type=industry_type)

    if ('ind' in request.args) and ('k' in request.args):
        industry_type = request.args['ind']
        k = request.args['k']
        r = industry_tickers(industry_type, k)
        tbl_list = r[1]
        names = r[0]
        html_tbl_list = [i.to_html(classes='df') for i in tbl_list]
        rr = zip(html_tbl_list, names)
        return render_template('industry.html', rr=rr,type='noneuro',industry_type=industry_type,)

@app.route('/api/v1/help',methods=['GET'])
def help():
  content = """
OptionGleaner API v1 -HELP
=======

####1.Exact search
/api/v1/resources?id=  
e.g. /api/v1/resources?id=GOOG  
return entire option list for google company  

####2.Random search
/api/v1/random?k=  
e.g. /api/v1/random?k=3  
return options of randomly chosen 3 companies

####3. Industry search
/api/v1/industry?ind=&k=  
e.g. /api/v1/industry?ind=Finance&k=3  
return options of randomly chosen 3 companies from Finance industry

####4. IV distribution plot
/api/v1/plot/id=&feature=  
e.g./api/v1/plot/id=goog&feature=IV  
draw a distribution plot of IV for options from goog  

####5. European options filter
&european=true  
e.g.   
/api/v1/resources?id=GOOG&european=true    
/api/v1/random?k=3&european=true  
/api/v1/industry?ind=Finance&k=3&european=true
/api/v1/plot/id=goog&feature=IV&european=true  
return corresponding European options
"""
  content = Markup(markdown.markdown(content))
  resource=['TickerList','IndustryList']
  return render_template('index.html', content=content,resource=resource)

@app.route('/api/v1/help/industrylist')
def industrylist():
    csv=pd.read_csv('industry_list.csv').to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                     "attachment; filename=industry_list.csv"})

@app.route('/api/v1/help/tickerlist')
def tickerlist():
    csv=pd.read_csv('ticker_list.csv').to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                     "attachment; filename=ticker_list.csv"})


@app.route('/api/v1/plot/',methods=['GET'])
def plot_raw():
    if ('id' in request.args)and ('feature' in request.args) and ('european' in request.args):
        ticker=request.args['id']
        feature=request.args['feature']
        raw_csv=get_one_ticker(ticker)
        csv=list(clean(raw_csv)[feature])
        title='Distribution Plot of {} for European Options from {}'.format(feature, ticker.upper())
        return render_template("plot.html", data=csv,name=title)

    if ('id' in request.args) and ('feature' in request.args):
        ticker=request.args['id']
        feature = request.args['feature']
        csv = list(get_one_ticker(ticker)[feature])
        title = 'Distribution Plot of {} for Options from {}'.format(feature,ticker.upper())
        return render_template("plot.html", data=csv, name=title)

    # img = io.BytesIO()
    # plt.figure()
    # plt.hist(csv['IV'])
    # plt.xlabel('IV')
    # plt.title('Distribution Plot of IV for {}'.format(ticker.upper()))
    # plt.savefig(img, format='png')
    # img.seek(0)
    # plot_url = base64.b64encode(img.getvalue()).decode()
    # return '<img src="data:image/png;base64,{}">'.format(plot_url)

app.run(debug=True)