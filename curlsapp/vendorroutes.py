import os,random,string,json, requests,re
#3rd party imports
from flask import Flask,render_template,request,redirect,flash,session,url_for
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash,check_password_hash
#import from local files
from curlsapp import app,db
from curlsapp.models import Vendors,Lga,State,Ven_style,Styles,Category,Products,Bookings,Order_details,Customer_orders,Payment,Newsletter

#generate random name for file uploads like pic and vid
def generate_name():
    filename = random.sample(string.ascii_letters,10)
    return "".join(filename)

#vendor pages
@app.route('/index/vendor')
def ven_signuppage():
    return render_template('vendor/ven_signuppage.html')

@app.route('/checkvenemail',methods=['GET','POST'])
def checkvenemail():
    if request.method == "GET":
        return "Kindly complete the form and input valid details"
    else:
        chkemail = request.form.get('email')
        if chkemail != None:
            pattern = '^[a-zA-Z0-9._%+-]+@[a-zA-Z.-]+\.[a-zA-Z]{2,}$'
            result = re.match(pattern, chkemail)
            if result:
                veninfo = Vendors.query.filter(Vendors.ven_email==chkemail).first()
                if veninfo == None:
                    rsp = {'status':'available', 'message':'Email is available, please proceed'}
                    return json.dumps(rsp)
                else:
                    rsp = {'status':'exists', 'message':'Email already exists, kindly Login'}
                    return json.dumps(rsp)
            else:
                rsp = {'status':'invalid', 'message':'Enter a valid email address'}
                return json.dumps(rsp)
        else:
            rsp = {'status':'empty', 'message':'Enter a valid email address'}
            return json.dumps(rsp)

@app.route('/venpwd_security', methods=["POST","GET"])
def venpwd_security():
    if request.method == "GET":
        return "Kindly complete the form and input valid details"
    else:
        chkpwd = request.form.get('password')
        if chkpwd == None:
            rsp = {'status':'empty', 'message':'Enter Password'}
            return json.dumps(rsp)
        else:
            password_regex = r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*])(?!.*\s).{8,}$"
            result = re.match(password_regex,chkpwd)
            if result:
                rsp = {'status':'ok', 'message':'password ok'}
                return json.dumps(rsp)
            else:
                rsp = {'status':'invalid', 'message':'password weak'}
                return json.dumps(rsp)

#letting the registration form submit to the route below as an intermediary to redirect to login or send back to ven page.
@app.route('/venregister',methods=['POST'])
def ven_register():
        vname = request.form.get('ven_name')
        vemail= request.form.get('ven_email')
        vpwd=request.form.get('ven_pwd')
        vconpwd=request.form.get('confirmpwd')
        hashed_pwd = generate_password_hash(vpwd)
        if vname !='' and vemail !='' and vpwd !='' and vconpwd !='':
            if vpwd == vconpwd:
                ven=Vendors(ven_name=vname,ven_email=vemail,ven_pwd=hashed_pwd)
                db.session.add(ven)
                db.session.commit()
                #get the id and save it in session
                venid=ven.ven_id
                session['vendor']=venid
                return redirect(url_for('ven_login'))
            else:
                flash("Passwords don't match")
                return redirect(url_for('ven_signuppage'))
        else:
            flash('Please complete all fields')
            return redirect(url_for('ven_signuppage'))

#retrieve form data, query db to check is user exists, chk if pwd match, redirect to vendor dashboard
@app.route('/vendor/login/', methods=["POST","GET"])
def ven_login():
    if request.method=="GET":
        return render_template('vendor/ven_login.html')
    else:
        vemail = request.form.get('vlogin_email')
        vpwd = request.form.get('vlogin_pwd')
        vdeets = db.session.query(Vendors).filter(Vendors.ven_email==vemail).first()
        if vdeets !=None: #theres a record
            pwd_indb=vdeets.ven_pwd
            chk =check_password_hash(pwd_indb,vpwd)
            if chk:
                id=vdeets.ven_id
                session['vendor']=id
                return redirect(url_for('ven_dashboard'))
            else:
                flash("Invalid credentials")
                return redirect(url_for('ven_login'))
        else:
            flash("Please complete fields")
            return redirect(url_for('ven_login'))
        
@app.route('/reset_vendorpassword',methods=['POST','GET'])
def reset_venpwd():
    if request.method == "GET":
        return render_template('vendor/reset_venpwd.html')
    else:
        email=request.form.get('vemail')
        newpwd = request.form.get('vpwd')
        confirmpwd = request.form.get('vconfirmpwd')
        # retrieve the data, check if the email supplied is their own email, if it isnt, pass a feedback. then check if the newpwd matches the confirm pwd, else pass feedback. 
        if email != '' and newpwd !='' and confirmpwd != '':
            veninfo = Vendors.query.filter(Vendors.ven_email==email).first()
            if veninfo != None:
                if newpwd == confirmpwd:
                    hashedpwd = generate_password_hash(newpwd)
                    veninfo.ven_pwd=hashedpwd
                    db.session.commit()
                    return redirect(url_for('ven_login'))
                else:
                    flash('Passwords must match')
                    return redirect(url_for('reset_venpwd'))
            else:
                flash("Invalid Email")
                return redirect(url_for('reset_venpwd'))
        else:
            flash('Please complete all fields')
            return redirect(url_for('reset_venpwd'))

@app.route('/vendor/dashboard/')
def ven_dashboard():
    if session.get('vendor') !=None:
        id=session['vendor']
        vdeets=db.session.query(Vendors).get(id)
        return render_template('vendor/ven_dashboard.html',vdeets=vdeets)
    else:
        return redirect(url_for('ven_login'))

@app.route('/vendor/logout/')
def ven_logout():
    if session.get('vendor') !=None:
        session.pop('vendor',None)
    return redirect(url_for('ven_signuppage'))


@app.route('/vendor/bookings/')
def ven_bookings():
    id=session['vendor']
    if id == None:
        return redirect(url_for('ven_login'))
    else:
        vdeets=db.session.query(Vendors).get(id)
        #retrieve the booking details from the order details and orders table. then display
        #allow the vendor to accept or cancel the appointment.
        
        # custbook = Order_details.query.join(Customer_orders).add_columns(Customer_orders).filter(Customer_orders.order_custid==custid,Customer_orders.custorder_status=='1',Order_details.order_bookid!=None).all()
        bookdeets = Bookings.query.join(Ven_style).add_columns(Ven_style).filter(Ven_style.venstyle_vendorid==id).all()
        query = db.session.query(Ven_style,Bookings,Order_details,Customer_orders).join(Bookings, Ven_style.ven_styleid==Bookings.booking_venstyleid).join(Order_details, Bookings.booking_id==Order_details.order_bookid).join(Customer_orders, Order_details.order_custorderid==Customer_orders.custorder_id)
        query = query.options(joinedload(Ven_style.bookservice),joinedload(Bookings.theorderdet), joinedload(Order_details.custorder))
        custbook = query.filter(Ven_style.venstyle_vendorid==id, Customer_orders.custorder_status=='1').order_by(Order_details.order_bookid.desc()).all()
        # test = Order_details.query.join(Customer_orders).add_columns(Customer_orders).filter(Order_details.bookinglink.booking_venstyleid.)
        return render_template('vendor/ven_bookings.html',vdeets=vdeets,bookdeets=bookdeets, custbook=custbook)


@app.route('/vendor/bookingdetails/<ordid>')
def ven_bookingdetails(ordid):
    id=session['vendor']
    if id == None:
        return redirect(url_for('ven_login'))
    else:
        vdeets=db.session.query(Vendors).get(id)
        history = Payment.query.filter(Payment.pay_custorderid==ordid).first()
        bookinfo = Order_details.query.filter(Order_details.order_custorderid==ordid).first()
        # details = Payment.query.join(Customer_orders).add_columns(Customer_orders).filter(Customer_orders.custorder_id==ordid).first()
        return render_template('vendor/ven_bookingdetails.html',vdeets=vdeets, history=history, bookinfo=bookinfo)

@app.route('/vendorbook_confirm/<bookid>')
def vendorbook_confirm(bookid):
    id=session.get('vendor')
    if id == None:
        return redirect(url_for('ven_login'))
    else:
        bookstat = Bookings.query.get_or_404(bookid)
        bookstat.booking_status='confirmed'
        db.session.commit()
        flash("Booking Confirmed",category='success')
        return redirect(url_for('ven_bookings'))

@app.route('/vendorbook_cancel/<bookid>')
def vendorbook_cancel(bookid):
    id=session.get('vendor')
    if id == None:
        return redirect(url_for('ven_login'))
    else:
        bookstat = Bookings.query.get_or_404(bookid)
        bookstat.booking_status='cancelled'
        db.session.commit()
        flash("Booking Cancelled", category='error')
        return redirect(url_for('ven_bookings'))

@app.route('/vendor/orders/')
def ven_orders():
    id=session['vendor']
    if id == None:
        return redirect(url_for('ven_login'))
    else:
        vdeets=db.session.query(Vendors).get(id)

        query = db.session.query(Customer_orders,Order_details,Products).join(Order_details, Customer_orders.custorder_id==Order_details.order_custorderid).join(Products, Order_details.order_prodid==Products.prod_id)
        query = query.options(joinedload(Customer_orders.orderitem), joinedload(Order_details.prodets))
        custprod = query.filter(Products.prod_venid==id, Customer_orders.custorder_status=='1').order_by(Customer_orders.custorder_id.desc()).all()
        return render_template('vendor/ven_orders.html',vdeets=vdeets, custprod=custprod)
    
@app.route('/vendor/orderhistory/<ordid>')
def ven_orderhistory(ordid):
    id=session['vendor']
    if id == None:
        return redirect(url_for('ven_login'))
    else:
        vdeets=db.session.query(Vendors).get(id)
        history = Payment.query.filter(Payment.pay_custorderid==ordid).first()
        # details = Payment.query.join(Customer_orders).add_columns(Customer_orders).filter(Customer_orders.custorder_id==ordid).first()
        return render_template('vendor/ven_orderhistory.html',vdeets=vdeets, history=history)

@app.route('/vendor/services/')
def ven_services():
    id=session['vendor']
    if id ==None:
        return redirect(url_for('ven_login'))
    else:
        data=db.session.query(Ven_style).filter(Ven_style.venstyle_vendorid==id,Ven_style.venstyle_status!='remove').all()
        vdeets=db.session.query(Vendors).get(id)
        return render_template('vendor/ven_services.html',data=data,vdeets=vdeets)
    
@app.route('/vendor/services/edit/<servid>', methods=["POST","GET"])
def edit_venservices(servid):
    id=session['vendor']
    if id ==None:
        return redirect(url_for('ven_login'))
    else:
        sdeets = Ven_style.query.get_or_404(servid)
        if request.method == "GET":
            #when they click on edit, it should display the information they previously had and update it. 
            vdeets=db.session.query(Vendors).get(id)
            stydata=db.session.query(Styles).all()   
            return render_template('vendor/update_venservice.html',stydata=stydata,sdeets=sdeets,vdeets=vdeets)
        else:
            styleid = request.form.get('sname')
            amt = request.form.get('styleamt')
            desc = request.form.get('styledesc')
            img = request.files['styleimg']
            vid = request.files['stylevid']
            allowed = ['.png', '.jpg','.jpeg','.mp4']
            if styleid != '' and amt != '' and img !='' and vid != '' and desc !='':
                fileimg=img.filename
                filevid=vid.filename
                name,ext=os.path.splitext(fileimg)
                x,y=os.path.splitext(filevid)
                if ext.lower() in allowed and y.lower() in allowed:
                    newfileimg=generate_name()+ext
                    newfilevid=generate_name()+y
                    img.save("curlsapp/static/uploads/styles/"+newfileimg)
                    vid.save("curlsapp/static/uploads/styles/"+newfilevid)
                    vstyobj = Ven_style.query.get_or_404(servid)
                    vstyobj.venstyle_styleid=styleid
                    vstyobj.venstyle_amt=amt
                    vstyobj.venstyle_pic=newfileimg
                    vstyobj.venstyle_vid=newfilevid
                    vstyobj.venstyle_desc=desc
                    vstyobj.venstyle_status='pending'
                    db.session.commit()
                    flash('Service updated successfully',category='success')
                    return redirect(url_for('edit_venservices',servid=sdeets.ven_styleid))
                else:
                    flash('Image extension not supported', category='error')
                    return redirect(url_for('edit_venservices', servid=sdeets.ven_styleid))
            else:
                flash('Please complete all fields', category='error')
                return redirect(url_for('edit_venservices', servid=sdeets.ven_styleid))
    
@app.route('/vendor/services/hide/<servid>')
def hide_venservices(servid):
    id=session['vendor']
    if id ==None:
        return redirect(url_for('ven_login'))
    else:
        #when they click on delete, i should remove it from display. that is the status will be 0. Cos only admin can delete services or products
        serv = Ven_style.query.get_or_404(servid)
        serv.venstyle_status='remove'
        db.session.commit()
        flash('Service successfully deleted')
        return redirect(url_for('ven_services'))


@app.route('/vendor/addstyles/',methods=["GET","POST"])
def add_styles():
    id=session.get('vendor')
    if id ==None:
        return redirect(url_for('ven_login'))
    else:
        if request.method=="GET":
            data=db.session.query(Styles).all()
            vdeets=db.session.query(Vendors).get(id)
            return render_template('vendor/ven_addstyles.html',data=data,vdeets=vdeets)
        else:
            styname=request.form.get('style_name')
            amt=request.form.get('style_amt')
            desc=request.form.get('style_desc')
            #retrieve img and video file
            img=request.files['style_img']
            fileimg=img.filename
            vid=request.files['style_vid']
            filevid=vid.filename
            allowed = ['.png', '.jpg','.jpeg','.mp4']
            if fileimg !='' and filevid !='' and styname!='' and amt!='' and desc !='':
                name,ext=os.path.splitext(fileimg)
                x,y=os.path.splitext(filevid)
                if ext.lower() in allowed and y.lower() in allowed:
                    newnameimg=generate_name()+ext
                    newnamevid=generate_name()+y
                    img.save("curlsapp/static/uploads/styles/"+newnameimg)
                    vid.save("curlsapp/static/uploads/styles/"+newnamevid)
                    v=Ven_style(venstyle_styleid=styname,venstyle_amt=amt,venstyle_pic=newnameimg,venstyle_vid=newnamevid,venstyle_desc=desc,venstyle_vendorid=id)
                    db.session.add(v)
                    db.session.commit()
                    flash("Service Successfully Added")
                    return redirect(url_for('add_styles'))
                else:
                    flash("Check file Format")
                    return redirect(url_for('add_styles'))
            else:
                flash("Please complete all fields")
                return redirect(url_for('add_styles'))


@app.route('/vendor/products/')
def ven_products():
    id=session['vendor']
    if id == id ==None:
        return redirect(url_for('ven_login'))
    else:
        data=db.session.query(Products).filter(Products.prod_venid==id, Products.prod_status!='remove').all()
        vdeets=db.session.query(Vendors).get(id)
        return render_template('/vendor/ven_products.html',data=data,vdeets=vdeets)

@app.route('/vendor/products/edit/<proid>',methods=['POST','GET'])
def edit_venproducts(proid):
    id=session['vendor']
    if id ==None:
        return redirect(url_for('ven_login'))
    else:
        pdeets = Products.query.get_or_404(proid)
        if request.method == "GET":
            vdeets=db.session.query(Vendors).get(id)
            pdata=db.session.query(Category).all()
            return render_template('vendor/update_venproduct.html',pdata=pdata, vdeets=vdeets,pdeets=pdeets)
        else:
            pname=request.form.get('prod_name')
            amt=request.form.get('prod_amt')
            qty=request.form.get('prod_qty')
            desc=request.form.get('prod_desc')
            cat=request.form.get('prod_cat')
            img=request.files['prod_img']
            allowed = ['.png', '.jpg','.jpeg']
            if pname !="" and amt !="" and desc !="" and cat !="" and img !="" and qty !="":
                filename=img.filename
                name,ext=os.path.splitext(filename)
                if ext.lower() in allowed:
                    newnameimg=generate_name()+ext
                    img.save("curlsapp/static/uploads/products/"+newnameimg)
                    prodobj = Products.query.get_or_404(proid)
                    prodobj.prod_name=pname
                    prodobj.prod_desc=desc
                    prodobj.prod_catid=cat
                    prodobj.prod_amt=amt
                    prodobj.prod_pic=newnameimg
                    prodobj.prod_venid=id
                    prodobj.prod_qty=qty
                    prodobj.prod_status='pending'
                    db.session.commit()
                    flash('Product updated successfully',category='success')
                    return redirect(url_for('edit_venproducts',proid=pdeets.prod_id))
                else:
                    flash('Image extension not supported',category='error')
                    return redirect(url_for('edit_venproducts',proid=pdeets.prod_id))
            else:
                flash('Please complete all fields',category='error')
                return redirect(url_for('edit_venproducts',proid=pdeets.prod_id))

@app.route('/vendor/products/hide/<proid>')
def hide_venproducts(proid):
    id=session['vendor']
    if id ==None:
        return redirect(url_for('ven_login'))
    else:
        prod = Products.query.get_or_404(proid)
        prod.prod_status='remove'
        db.session.commit()
        flash('Product successfully deleted')
        return redirect(url_for('ven_products'))

@app.route('/vendor/addproducts/',methods=["GET","POST"])
def add_products():
    id=session['vendor']
    if id ==None:
        return redirect(url_for('ven_login'))
    else:
        if request.method=="GET":
            data=db.session.query(Category).all()
            vdeets=db.session.query(Vendors).get(id)
            return render_template('vendor/ven_addproducts.html',data=data,vdeets=vdeets)
        else:
            prodname=request.form.get('prod_name')
            amt=request.form.get('prod_amt')
            qty=request.form.get('prod_qty')
            desc=request.form.get('prod_desc')
            cat=request.form.get('prod_cat')
            #retrieve img
            img=request.files['prod_img']

            allowed = ['.png', '.jpg','.jpeg']
            if prodname !="" and amt !="" and desc !="" and cat !="" and img !="" and qty !="":
                filename=img.filename
                name,ext=os.path.splitext(filename)
                if ext.lower() in allowed:
                    newnameimg=generate_name()+ext
                    img.save("curlsapp/static/uploads/products/"+newnameimg)
                    prods = Products(prod_name=prodname,prod_desc=desc,prod_catid=cat,prod_amt=amt,prod_pic=newnameimg,prod_venid=id,prod_qty=qty)
                    db.session.add(prods)
                    db.session.commit()
                    flash("Product Successfully Added")
                    return redirect(url_for('add_products'))
                else:
                    flash("Check file Format")
                    return redirect(url_for('add_products'))
            else:
                flash("Please complete all fields")
                return redirect(url_for('add_products'))



@app.route('/load_venlga/<stateid>')
def load_venlga(stateid):
    lgas = db.session.query(Lga).filter(Lga.lga_stateid==stateid).all()
    data2send = "<select class='form-select border-info' name='lga'>"
    for s in lgas:
        data2send = data2send+f"<option value='{s.lga_id}'>"+s.lga_name +"</option>"
    
    data2send = data2send + "</select>"

    return data2send


#write query to filter and display the vendor info in get, then post to update
@app.route('/vendor/profile/',methods=["POST","GET"])
def ven_profile():
    id=session['vendor']
    if id ==None:
        return redirect(url_for('ven_login'))
    else:
        if request.method == 'GET':
            vdeets=db.session.query(Vendors).filter(Vendors.ven_id==id).first()
            ldata=db.session.query(Lga).all()
            sdata=db.session.query(State).all()
            return render_template('/vendor/ven_profile.html',vdeets=vdeets,ldata=ldata,sdata=sdata)
        else:
            vphone=request.form.get('phone')
            vaddress=request.form.get('address')
            desc=request.form.get('description')
            sm=request.form.get('social1')
            sm2=request.form.get('social2')
            lga=request.form.get('lga')
            state=request.form.get('state')
            #to retrieve the picture file
            file = request.files['salonpix']
            if vphone != '' and vaddress != '' and desc != '' and sm != '' and sm2 != '' and lga != '' and state != '' and file != '':
                filename=file.filename
                allowed = ['.png', '.jpg','.jpeg']
                name,ext =os.path.splitext(filename)
                if ext.lower() in allowed:
                    ids=str(id)
                    newname = generate_name()+ids+ext
                    file.save("curlsapp/static/uploads/"+newname)
                    venobj=db.session.query(Vendors).get(id)
                    venobj.ven_phone=vphone
                    venobj.ven_address=vaddress
                    venobj.ven_workdesc=desc
                    venobj.ven_socialmedia=sm
                    venobj.ven_socialmedia2=sm2
                    venobj.ven_lgaid=lga
                    venobj.ven_stateid=state
                    venobj.ven_salonpix=newname
                    db.session.commit()
                    flash('Profile Updated',category='success')
                    return redirect(url_for('ven_profile'))
                else:
                    flash("Image extension not supported",category='error')
                    return redirect(url_for('ven_profile'))
            else:
                flash("Please complete all fields", category='error')
                return redirect(url_for('ven_profile'))
                
           
            