from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta, date
from sqlalchemy import func
from clinic import app, db
from clinic.models import User, Detail, Patient, Medicine, Announcement, Worklog
from clinic.forms import PatientForm, MedicineForm, DetailForm, AddannouncementForm, ChangePatientForm, AddWorkLogForm, ChangeDetailForm
import uuid
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
import pandas as pd
import base64
from io import BytesIO
from matplotlib.figure import Figure
import re
from dateutil.parser import parse
from sqlalchemy import extract  

class HomeView(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('login'))

admin = Admin(app, name="管理员")
admin.add_view(ModelView(User, db.session, name="大夫")) 
admin.add_view(ModelView(Patient, db.session, name="患者")) 
admin.add_view(ModelView(Detail, db.session, name="患者病患信息")) 
admin.add_view(ModelView(Medicine, db.session, name='药品'))
admin.add_view(ModelView(Worklog, db.session, name="工作日志")) 
admin.add_view(ModelView(Announcement, db.session, name='公告'))
admin.add_view(HomeView(name='返回主页'))

@app.route('/explain')
def explain():
    return render_template('explain.html')

@app.route("/logout") 
def logout(): 
    logout_user() 
    return redirect(url_for('login'))   


@app.route('/', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        user = db.session.query(User.name).first()
        return redirect(url_for('doctor_information', name=user.name))
    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')
        user = User.query.filter_by(name=user).first()
        if user and user.password == password:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('doctor_information', name=user.name))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login')

@app.route("/home-for/<string:name>", methods=['POST', 'GET'])
@login_required 
def doctor_information(name):
    OutComeData.findmatchdata1()
    IncomeData.findmatchdata()
    user = User.query.filter_by(name=name).first_or_404()
    amount_patient = len(db.session.query(Patient.name).all())
    mylist = db.session.query(Patient.name).all() 
    mylist1 = len(list(dict.fromkeys(mylist)))  
    current_time = datetime.now() 
    time = timedelta(weeks = 4) 
    four_weeks_ago = current_time - time 
    filter_by_month = db.session.query(Patient.name).filter(Patient.create > four_weeks_ago).all() 
    filter_by_month_1 = len(list(dict.fromkeys(filter_by_month))) 
    filter_by_today_1 = len(db.session.query(Detail).filter(func.date(Detail.Date_of_diagnosis) == date.today()).all())
    Money_today_1 = OutComeData.TotalOutComeToday()
    Money_month_1 = OutComeData.TotalOutComeMonth()
    Money_earn_today_1 = IncomeData.TotalIncomeToday()
    Money_earn_month_1 = IncomeData.TotalIncomeMonth()
    value=Worklog.query.filter_by(author=user).order_by(Worklog.date_posted.desc())
    return render_template('main.html', user=user, mylist1=mylist1, amount_patient=amount_patient, 
    filter_by_month_1=filter_by_month_1, filter_by_today_1=filter_by_today_1, Money_today_1=Money_today_1, Money_month_1=Money_month_1,
    Money_earn_1=Money_earn_today_1, Money_earn_month_1=Money_earn_month_1, values=value, announcements=Announcement.query.all())    

@app.route("/patient") 
@login_required 
def patient(): 
    page = request.args.get('page', 1, type=int) 
    patients = Patient.query.order_by(Patient.create.desc()).paginate(page=page, per_page=15) 
    return render_template('patient.html', patients=patients, announcements=Announcement.query.all())

PatientDictionary = {}
TotalPatientDictionary = {}
datarefreshLog = []
todayPatient = []

def converter1(date: str) -> str:
    return tuple(int(item) for item in date.split('-'))
IncomeDictionary = {}
IncomeDictionarymonthly = {}
class Income_data():
    def __init__(self):
        self.self = self

    def getIncome(self, args):
        try:
            match = re.findall(r'\d+', str(args))
            return int(match[0])
        except IndexError:
            return 0

    def findmatchdata(self):
        now = converter1(str(datetime.now())[:10])
        IncomeDictionary[now] = []
        IncomeDictionarymonthly[now] = []
        IncomeData.IncomeDaily()
        IncomeData.IncomeMonth()

    def IncomeDaily(self):
        now = converter1(str(datetime.now())[:10])
        for x in db.session.query(Detail.cost1).filter(func.date(Detail.Date_of_diagnosis) == date.today()).all():
            IncomeDictionary[now].append(IncomeData.getIncome(x))
        for y in db.session.query(Detail.cost2).filter(func.date(Detail.Date_of_diagnosis) == date.today()).all():
            IncomeDictionary[now].append(IncomeData.getIncome(y))
        for z in db.session.query(Detail.cost3).filter(func.date(Detail.Date_of_diagnosis) == date.today()).all():
            IncomeDictionary[now].append(IncomeData.getIncome(z))

    def IncomeMonth(self):
        month = datetime.now().month
        year = datetime.now().year
        now = converter1(str(datetime.now())[:10])
        for i in db.session.query(Detail.cost1).filter(extract('year', Detail.Date_of_diagnosis)==year).filter(extract('month', Detail.Date_of_diagnosis)==month).all():
            IncomeDictionarymonthly[now].append(IncomeData.getIncome(i))
        for x in db.session.query(Detail.cost2).filter(extract('year', Detail.Date_of_diagnosis)==year).filter(extract('month', Detail.Date_of_diagnosis)==month).all():
            IncomeDictionarymonthly[now].append(IncomeData.getIncome(x))
        for y in db.session.query(Detail.cost3).filter(extract('year', Detail.Date_of_diagnosis)==year).filter(extract('month', Detail.Date_of_diagnosis)==month).all():
            IncomeDictionarymonthly[now].append(IncomeData.getIncome(y))

    def saveData_csv(self, date, patient, cost1, cost2, cost3):
        arr = {'日期': [date], '患者': [patient], '金额1': [cost1], '金额2': [cost2], '金额3': [cost3]}
        df = pd.DataFrame(arr, columns= ['日期', '患者', '金额1', '金额2', '金额3'])
        df.to_csv('Income.csv', index = True, header=True)

    def TotalIncomeToday(self):
        now = converter1(str(datetime.now())[:10])
        try:
            return sum(IncomeDictionary[now])
        except TypeError:
            IncomeDictionary[now] = []
            return 0
    
    def TotalIncomeMonth(self):
        now = converter1(str(datetime.now())[:10])
        try:
            return sum(IncomeDictionarymonthly[now])
        except TypeError:
            IncomeData.IncomeMonth()
            return 0

IncomeData = Income_data()
IncomeData.findmatchdata()

OutComeDictionary = {}
OutComeDictionaryMonthly = {}
class OutComeData1():
    def __init__(self):
        self.self = self

    def getOutcome(self, args):
        try:
            match = re.findall(r'\d+', str(args))
            return int(match[0])
        except IndexError:
            return 0

    def findmatchdata1(self):
        now = converter1(str(datetime.now())[:10])
        OutComeDictionary[now] = []
        OutComeDictionaryMonthly[now] = []
        OutComeData.OutcomeDaily()
        OutComeData.OutcomeMonth()

    def OutcomeDaily(self):
        now = converter1(str(datetime.now())[:10])
        for x in db.session.query(Medicine.Price).filter(func.date(Medicine.time_get) == date.today()).all():
            OutComeDictionary[now].append(int(str((str(x)[2:-3])).replace(',', '')))
    
    def OutcomeMonth(self):
        month = datetime.now().month
        year = datetime.now().year
        now = converter1(str(datetime.now())[:10])
        for i in db.session.query(Medicine.Price).filter(extract('year', Medicine.time_get)==year).filter(extract('month', Medicine.time_get)==month).all():
            OutComeDictionaryMonthly[now].append(int(str((str(i)[2:-3])).replace(',', '')))

    def saveData_csv(self, date, medicine, cost, vendor, doctor):
        arr = {'日期': [date], '药品': [medicine], '金额': [cost], '供应商': [vendor], '添加者': [doctor]}
        df = pd.DataFrame(arr, columns= ['日期', '患者', '金额', '供应商', '添加者'])
        df.to_csv('Outcome.csv', index = True, header=True)

    def TotalOutComeToday(self):
        now = converter1(str(datetime.now())[:10])
        try:
            return sum(OutComeDictionary[now])
        except TypeError:
            OutComeDictionary[now] = []
            return 0
    
    def TotalOutComeMonth(self):
        now = converter1(str(datetime.now())[:10])
        try:
            return sum(OutComeDictionaryMonthly[now])
        except TypeError:
            OutComeDictionaryMonthly[now] = []
            return 0

OutComeData = OutComeData1()
OutComeData.findmatchdata1()

token = uuid.uuid4()
token_dict = []
token_dict.append(token)
log = {}

@app.route('/clinic-admin', methods=['GET','POST'])
@login_required
def clinic_admin():
    return redirect('admin')

@app.route('/clinic-admin/%s' % token_dict[-1], methods=['GET','POST'])
@login_required
def clinic_admin_page():
    now = datetime.now()
    time = [i for i in log.keys()]
    if int(str(now)[11:13]) - int(time[-1]) > 8:
        return redirect('/clinic-admin')
    fig = Figure()
    data = pd.read_csv('patient.csv')
    ax = fig.subplots()
    x = data['date']
    y = data['count']
    ax.plot(x, y)
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return render_template("clinic_admin_page.html", image=data)

a = uuid.uuid4()
def checkValidsubId(subid: str) -> str: # subid should be unique value
    Allsubid = list(db.session.query(Patient.subid))
    while subid in Allsubid:
        subid = uuid.uuid4()
        return subid.hex
    return subid

@app.route('/allpatient')
@login_required  
def allpatient():
    return render_template('find_patient.html', values=Patient.query.all())   

@app.route("/addpatient", methods=['GET', 'POST']) 
@login_required 
def addpatient(): 
    form = PatientForm() 
    if form.validate_on_submit(): 
        patient1 = Patient(name=form.name.data, number=form.number.data, gender=form.gender.data, ID_Card=form.ID_Card.data, street=form.street.data)   
        ID = (patient1.ID_Card) 
        subid = checkValidsubId(a.hex)
        patient = Patient(subid=subid, name=form.name.data, number=form.number.data, gender=form.gender.data, ID_Card=form.ID_Card.data, 
        year = ID[slice(6,10)], month = ID[slice(10, 12)], day = ID[slice(12, 14)], street=form.street.data, doctor=current_user)   
        db.session.add(patient) 
        db.session.commit()
        time = datetime.now()
        day = time.strftime("%A") 
        date = day[:3] 
        file = open('log.txt','a')
        file.writelines('%s %s/%s/%s 患者："%s" 个人信息已被医生："%s" 加入进数据库.\n' % (date, time.month, time.day, time.year, patient.name, patient.doctor.name))
        file.close()
        flash('此患者已被加入进数据库当中', 'success') 
        return redirect(url_for('patient')) 
    return render_template('add_patient.html', title='Add Patient', form=form, announcements=Announcement.query.all()) 

@app.route("/update-patient/<string:subid>", methods=['GET', 'POST'])  
@login_required 
def update_patient(subid):
    patient = Patient.query.filter_by(subid=subid).first_or_404()
    form = ChangePatientForm() 
    if form.validate_on_submit(): 
        patient.number = form.number.data 
        patient.street = form.street.data
        db.session.commit()
        time = datetime.now()
        day = time.strftime("%A")
        date = day[:3] 
        file = open('log.txt','a')
        file.writelines('%s %s/%s/%s 患者："%s" 个人信息被医生："%s" 更改.\n' % (date, time.month, time.day, time.year, patient.name, patient.doctor.name))
        file.close()
        flash('患者信息已更改!', 'success') 
        return redirect(url_for('patient_info', subid=patient.subid))
    elif request.method == 'GET':
        form.number.data = patient.number
        form.street.data = patient.street
    return render_template('change_patient.html', title='Update Patient',
                           form=form, legend='Update Patient', announcements=Announcement.query.all()) 

@app.route("/update-patient-detail/<int:id>", methods=['GET', 'POST'])  
@login_required 
def update_patient_detail(id):
    detail = Detail.query.get(id)
    form = ChangeDetailForm() 
    if form.validate_on_submit(): 
        detail.Symptom = form.Symptom.data
        detail.Check_result = form.Check_result.data
        detail.Preliminary_treatment_plan = form.Preliminary_treatment_plan.data
        db.session.commit()
        flash('患者信息已更改!', 'success') 
        return redirect(url_for('patient_info_detail', subid=detail.subid, id=detail.id))
    elif request.method == 'GET':
        form.Symptom.data = detail.Symptom
        form.Check_result.data = detail.Check_result
        form.Preliminary_treatment_plan.data = detail.Preliminary_treatment_plan
    return render_template('change_patient_detail.html', title='Update Patient',
                           form=form, legend='Update Patient', announcements=Announcement.query.all()) 

@app.route("/delete-patient-detail/<string:subid>/<int:id>", methods=['GET', 'POST']) 
@login_required
def delete_patient_detail(subid, id): 
    detail = Detail.query.filter_by(id=id).first_or_404()
    db.session.delete(detail) 
    db.session.commit() 
    now = converter1(str(datetime.now())[:10])
    flash('此患者病患信息已被删除')
    return redirect(url_for('patient_info', subid=subid)) 

@app.route("/patient-info/<string:subid>") 
@login_required
def patient_info(subid): 
    patient = Patient.query.filter_by(subid = subid).first_or_404()
    detail = Detail.query.filter_by(subid = subid).order_by(Detail.Date_of_diagnosis.desc()).all()
    return render_template('patient_info.html', patient=patient, value = detail, announcements=Announcement.query.all())    

@app.route("/patient/<string:subid>/<int:id>") 
@login_required
def patient_info_detail(subid, id): 
    detail = Detail.query.get(id)
    return render_template('patient_info_detail.html', value = detail, announcements=Announcement.query.all())    

@app.errorhandler(404)
def not_found(e):
  return render_template('custom_page.html'), 404

@app.route('/404/more')
def more_404():
    return render_template('more_404.html')

@app.route("/patient-detail/<string:subid>", methods=['GET', 'POST']) 
@login_required 
def patientdetail(subid): 
    patient = Patient.query.filter_by(subid=subid).first_or_404()
    detail = Detail.query.filter_by(subid=subid).first_or_404()
    return render_template('patient_detail.html', detail=detail, patient=patient, announcements=Announcement.query.all())

symptom_suggestion = {}
 
def stat(form):
    symptom = db.session.query(Detail.Symptom) # factor
    result = db.session.query(Detail.Check_result) # result
    for res in result:
        for sym in symptom: 
            symptom_suggestion[sym] = res
    while len(symptom_suggestion) > 10:
        for k in symptom_suggestion.keys():
            if form[0] in k:
                return str(symptom_suggestion[k])
    else:
        return form[1]

@app.route("/add-patient-detail/<string:subid>", methods=['GET', 'POST']) 
@login_required  
def add_patient_detail(subid): 
    form = DetailForm()   
    if form.validate_on_submit():  
        patient = Patient.query.filter_by(subid=subid).first_or_404()  
        if request.method == 'POST':
            description = request.form.get('description') 
            detail = Detail(subid=patient.subid, Symptom=form.Symptom.data, Check_result=form.Check_result.data, 
            Preliminary_treatment_plan=form.Preliminary_treatment_plan.data, description=description, cost1=form.cost1.data, cost2=form.cost2.data, cost3=form.cost3.data, tag=form.tag.data, user=current_user, owner=patient)
            db.session.add(detail) 
            db.session.commit() 
            time = datetime.now()
            IncomeData.saveData_csv(time, patient.name, detail.cost1, detail.cost2, detail.cost3)
            day = time.strftime("%A")
            date = day[:3] 
            file = open('log.txt','a')
            file.writelines('%s %s/%s/%s 患者："%s" 病患信息已被医生："%s" 加入进数据库.\n' % (date, time.month, time.day, time.year, patient.name, detail.user.name))
            file.close()
        flash('此患者已被加入进数据库当中', 'success') 
        return redirect(url_for('patient'))     
    return render_template('add_patient_detail.html', title='Add Patient Detail', form=form, announcements=Announcement.query.all())   

@app.route("/patient-detail-update/<int:patient_id>", methods=['GET', 'POST'])  
@login_required   
def patient_detail_update(patient_id): 
    detail = Detail.query.get_or_404(patient_id)   
    patient = Patient.query.get_or_404(patient_id)
    form = DetailForm()  
    if form.validate_on_submit(): 
        detail.Symptom = form.Symptom.data 
        detail.Check_result = form.Check_result.data 
        detail.Preliminary_treatment_plan = form.Preliminary_treatment_plan.data 
        detail.tag = form.tag.data
        db.session.commit()
        time = datetime.now()
        day = time.strftime("%A")
        date = day[:3] 
        file = open('log.txt','a')
        file.writelines('%s %s/%s/%s 患者："%s" 病患信息已被医生："%s" 更改.\n' % (date, time.month, time.day, time.year, patient.name, detail.user.name))
        file.close()
        flash('患者信息已更改!', 'success') 
        return redirect(url_for('patientdetail', patient_id=detail.id))
    elif request.method == 'GET':
        form.Symptom.data = detail.Symptom
        form.Check_result.data = detail.Check_result
        form.Preliminary_treatment_plan.data = detail.Preliminary_treatment_plan 
        form.tag.data = detail.tag
    IncomeData.findmatchdata()
    return render_template('add_patient_detail.html', title='Update Patient-Detail',
                           form=form, legend='Update Patient-Detail', patient=patient, announcements=Announcement.query.all()) 
 
@app.route("/medicine") 
@login_required
def medicine_info():
    page = request.args.get('page', 1, type=int) # get all the posts from db file
    medicines = Medicine.query.order_by(Medicine.time_get.desc()).paginate(page=page, per_page=10)
    return render_template('medicine.html', medicines=medicines, announcements=Announcement.query.all()) 

@app.route('/allmedicine')
@login_required 
def allmedicine():
    return render_template('find_medicine.html', values=Medicine.query.all(), announcements=Announcement.query.all())  

@app.route('/medicine-info-for/<string:Medicine_name>')
@login_required  
def medicine_info_for(Medicine_name):
    medicine = Medicine.query.filter_by(id=id).first_or_404()
    return render_template('find_medicine_history.html', medicine=medicine, values=Medicine.query.filter_by(Medicine_name=Medicine_name), announcements=Announcement.query.all()) 

@app.route("/medicine/<int:id>") 
@login_required
def medicine(id):  
    medicine = Medicine.query.filter_by(id=id).first_or_404() 
    return render_template('medicine_info.html', medicine=medicine, announcements=Announcement.query.all()) 

@app.route("/addmedicine", methods=['GET', 'POST']) 
@login_required
def add_medicine():
    form = MedicineForm() 
    if form.validate_on_submit(): 
        if request.method == 'POST':
            deadline = request.form.get('Deadline')
            medicine = Medicine(Vendor=form.Vendor.data, Quantity=form.Quantity.data, 
            Medicine_name=form.Medicine_name.data, Deadline=deadline, Price=form.Price.data, How_to_use=form.How_to_use.data,
            doctor=current_user) 
            db.session.add(medicine)
            db.session.commit() 
            OutComeData.saveData_csv(datetime.now(), medicine.Medicine_name, medicine.Price, medicine.Vendor, medicine.doctor.name)
            flash('此药物已被加入进数据库当中', 'success') 
            return redirect(url_for('allmedicine'))
    return render_template('add_medicine.html', title='Add Medicine', form=form, announcements=Announcement.query.all())  

@app.route("/update-medicine/<int:medicine_id>", methods=['GET', 'POST']) 
@login_required 
def update_medicine(medicine_id): 
    medicine = Medicine.query.get_or_404(medicine_id)  
    form = MedicineForm() 
    if form.validate_on_submit(): 
        medicine.Vendor = form.Vendor.data 
        medicine.Quantity = form.Quantity.data 
        medicine.Medicine_name = form.Medicine_name.data 
        medicine.Price = form.Price.data 
        flash('药物信息已更改!', 'success')  
        db.session.commit()
        return redirect(url_for('medicine', Medicine_name=medicine.Medicine_name))
    elif request.method == 'GET':
        form.Vendor.data = medicine.Vendor
        form.Quantity.data = medicine.Quantity
        form.Medicine_name.data = medicine.Medicine_name
        form.Price.data = medicine.Price
    return render_template('change_medicine.html', title='Update Medicine',
                           form=form, legend='Update Medicine', announcements=Announcement.query.all()) 
 
@app.route("/delete-medicine/<int:medicine_id>", methods=['POST', 'GET']) 
@login_required 
def delete_medicine(medicine_id): 
    medicine = Medicine.query.get_or_404(medicine_id) 
    db.session.delete(medicine) 
    db.session.commit() 
    now = converter1(str(datetime.now())[:10])
    OutComeDictionary[now].remove(IncomeData.getIncome(Medicine.Price))
    OutComeDictionaryMonthly[now].remove(IncomeData.getIncome(Medicine.Price))
    flash('药物已被删除!', 'success') 
    return redirect(url_for('allmedicine'))

@app.route('/worklog')
@login_required  
def worklog():  
    page = request.args.get('page', 1, type=int) 
    worklogs = Worklog.query.order_by(Worklog.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('worklog.html', worklogs=worklogs, announcements=Announcement.query.all())
  
@app.route('/add-work-log/<string:name>', methods=['GET', 'POST'])
@login_required  
def add_work_log(name): 
    form = AddWorkLogForm() 
    if form.validate_on_submit():  
        worklog = Worklog(title=form.title.data, body=form.body.data, tag=form.tag.data, author=current_user) 
        db.session.add(worklog) 
        db.session.commit() 
        flash('工作日志已被加入进数据库当中', 'success')  
        return redirect(url_for('doctor_information', name=worklog.author.name))    
    return render_template('add_work_log.html', title='Add Worklog', form=form, announcements=Announcement.query.all()) 

@app.route('/find-all-work-log', methods=['GET']) 
@login_required 
def find_all_work_log():
    if current_user.id != 1:
        return render_template('forbidden.html') 
    else:
        return render_template('find_work_log.html', values=Worklog.query.all()) 

@app.route('/work-log-info/<string:name>', methods=['GET', 'POST'])  
@login_required    
def the_work_log_for(name):      
    user = User.query.filter_by(name=name).first_or_404()
    return render_template('find_work_log.html', values=Worklog.query.filter_by(author=user), announcements=Announcement.query.all())  

@app.route('/work/log-for/the/doctor/id/<int:worklog_id>') 
@login_required 
def work_log_for_the_doctor_id(worklog_id):  
    worklog = Worklog.query.get_or_404(worklog_id)
    return render_template('worklog_info.html', worklog=worklog,announcements=Announcement.query.all())      

@app.route('/add-announcement', methods=['GET', 'POST'])
@login_required  
def add_announcement(): 
    if current_user.id != 1:
        return render_template('forbidden.html',announcements=Announcement.query.all())
    else:
        form = AddannouncementForm() 
        if form.validate_on_submit():  
            announcement = Announcement(title=form.title.data, body=form.body.data, author=current_user) 
            db.session.add(announcement)  
            db.session.commit() 
            flash('工作日志已被加入进数据库当中', 'success')  
            return redirect(url_for('doctor_information', name=announcement.author.name))     
        return render_template('add_announcement.html', title='Add Announcement', form=form, announcements=Announcement.query.all()) 

@app.route('/announcement/<int:announcement_id>') 
@login_required 
def announcement(announcement_id):  
    announcement = Announcement.query.get_or_404(announcement_id)
    return render_template('announcement-info.html', announcement=announcement, announcements=Announcement.query.all()) 
