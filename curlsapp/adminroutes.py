from flask import Flask,render_template,request,session,url_for,flash,redirect
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash,check_password_hash
#local imports
from curlsapp import app,db
from curlsapp.models import Admin,Vendors,Styles,Ven_style,Category,Products,Payment,Customers,Customer_orders,Messages,Order_details,Bookings


# @app.route('/admin/register/',methods=["GET","POST"])
# def admin_reg():
    # if request.method=="GET":
    #     return render_template('admin/adminreg.html')
    # else:
    #     uname=request.form.get('username')
    #     pwd=request.form.get('password')
    #     hashed_pwd = generate_password_hash(pwd)
    #     #insert into db using ORM, create an instance, assign attributes,add,commit.
    #     if uname !='' and pwd !='':
    #         ad=Admin(admin_username=uname,admin_pwd=hashed_pwd)
    #         db.session.add(ad)
    #         db.session.commit()
    #         return redirect(url_for('admin_login'))
    #     else:
    #         flash("All fields required")
    #         return redirect(url_for('admin_reg'))

@app.route('/admin/login/',methods=["POST","GET"])
def admin_login():
    if request.method=="GET":
        return render_template('admin/adminlogin.html')
    else:
        username=request.form.get('username')
        pwd=request.form.get('password')
        
        udeet = db.session.query(Admin).filter(Admin.admin_username==username).first()
        if udeet !=None:
            pwd_indb=udeet.admin_pwd
            chk = check_password_hash(pwd_indb,pwd)
            if chk:
                id=udeet.admin_id
                session['admin']=id
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid Credentials")
                return redirect(url_for('admin_login'))
        else:
            return redirect(url_for('admin_login'))



@app.route('/admin/dashboard/')
def admin_dashboard():
    if session.get('admin') !=None:
        id = session['admin']
        adeets=db.session.query(Admin).get(id)
        cust = Customers.query.all()
        ven = Vendors.query.all()
        orders = Customer_orders.query.all()
        return render_template('admin/admin_dashboard.html',adeets=adeets,cust=cust,ven=ven,orders=orders)
    else:
        return redirect(url_for('admin_login'))
    
    
@app.route('/admin/orders')
def dashboard_orders():
    id = session['admin']
    if id == None:
        return redirect(url_for('admin_login'))
    else:
        adeets=db.session.query(Admin).get(id)
      
        # getting all the orders. join payment, custorders and orderdetails.
        query = db.session.query(Payment,Customer_orders).join(Customer_orders, Payment.pay_custorderid==Customer_orders.custorder_id)
        query = query.options(joinedload(Payment.odetails))
        allorders = query.order_by(Customer_orders.custorder_id.desc()).all()
        return render_template('admin/dashboard_orders.html',adeets=adeets,allorders=allorders)
    
@app.route('/admin/orders/orderdetails/<ordid>')
def allorders_details(ordid):
    id = session['admin']
    if id == None:
        return redirect(url_for('admin_login'))
    else:
        odeets = Order_details.query.filter(Order_details.order_custorderid==ordid).all()
        info = Customer_orders.query.get_or_404(ordid)
        return render_template('admin/allorders_details.html', odeets=odeets, info=info)
   

@app.route('/admin/bookings')
def dashboard_bookings():
    id = session['admin']
    if id == None:
        return redirect(url_for('admin_login'))
    else:
       
        query = db.session.query(Customer_orders,Order_details).join(Order_details, Customer_orders.custorder_id==Order_details.order_custorderid)
        query = query.options(joinedload(Customer_orders.orderitem))
        allbooks = query.filter(Order_details.order_bookid!=None).order_by(Customer_orders.custorder_id.desc()).all()

        return render_template('admin/dashboard_bookings.html', allbooks=allbooks)

@app.route('/admin/logout/')
def admin_logout():
    if session.get('admin') !=None:
        session.pop('admin',None)
    return redirect(url_for('admin_login'))

@app.route('/admin/managevendors')
def manage_vendors():
    id = session['admin']
    if id == None:
        return redirect(url_for('admin_login'))
    else:
        vdata = Vendors.query.order_by(Vendors.ven_regdate.desc()).all()
        return render_template('admin/manage_vendors.html',vdata=vdata)

    
@app.route('/admin/managevendors/vetvendor/<venid>')
def vet_vendor(venid):
    id = session['admin']
    if id == None:
        return redirect(url_for('admin_login'))
    else:
        vdeet = Vendors.query.get(venid)
        return render_template('admin/vet_vendor.html',vdeet=vdeet)
    
@app.route('/admin/approve_vendor',methods=["POST", "GET"])
def approve_vendor():
    if session.get('admin') !=None:
        newstatus = request.form.get('status')
        venid = request.form.get('venid')
        s = db.session.query(Vendors).get(venid)
        s.ven_status=newstatus
        db.session.commit()
        flash("Vendor Display Status updated")
        return redirect(url_for('manage_vendors'))
    else:
        return redirect(url_for('admin_login'))



    #screen vendor services 

@app.route('/admin/screen_services')
def screen_services():
    id = session['admin']
    if id == None:
        return redirect(url_for('admin_login'))
    else:
        vdata=Ven_style.query.order_by(Ven_style.ven_styleid.desc()).filter(Ven_style.venstyle_status!='remove').all()
        return render_template('admin/screen_services.html',vdata=vdata)
    

@app.route('/admin/vetservices/<venid>/')
def vet_vendorservices(venid):
    if session.get('admin') !=None:
        vdeet =Ven_style.query.get(venid)
        return render_template('admin/vet_vendorservice.html',vdeet=vdeet)
    else:
        return redirect(url_for('admin_login'))
    
@app.route('/admin/update_venstatus',methods=["POST", "GET"])
def update_venstatus():
    if session.get('admin') !=None:
        newstatus = request.form.get('status')
        styleid = request.form.get('styleid')
        s = db.session.query(Ven_style).get(styleid)
        s.venstyle_status=newstatus
        db.session.commit()
        flash("Vendor style status successfully updated")
        return redirect(url_for('screen_services'))
    else:
        return redirect(url_for('admin_login'))

@app.route('/admin/deleteven_service/<venid>')
def del_venservice(venid):
    if session.get('admin') !=None:
        vdeet =Ven_style.query.get_or_404(venid)
        db.session.delete(vdeet)
        db.session.commit()
        flash('Vendor service deleted successfully')
        return redirect(url_for('screen_services'))
    else:
        return redirect(url_for('admin_login'))

# screen vendor products
@app.route('/admin/screen_products')
def screen_products():
    id = session['admin']
    if id == None:
        return redirect(url_for('admin_login'))
    else:
        pdata = Products.query.join(Vendors).add_columns(Vendors).filter(Vendors.ven_status=='1',Products.prod_status!='remove').order_by(Products.prod_id.desc()).all()
        # pdata = Products.query.order_by(Products.prod_id.desc()).all()
        return render_template('admin/screen_products.html',pdata=pdata)
    
@app.route('/admin/vetproducts/<prodid>', methods=["POST", "GET"])
def vet_products(prodid):
    id = session['admin']
    if id == None:
        return redirect(url_for('admin_login'))
    else:
        if request.method == "GET":
            pdeet =Products.query.get(prodid)
            return render_template('admin/vet_products.html',pdeet=pdeet)
        else:
            newstatus = request.form.get('status')
            prodid = request.form.get('prodid')
            p = db.session.query(Products).get(prodid)
            p.prod_status=newstatus
            db.session.commit()
            flash("Vendor Product status successfully updated")
            return redirect(url_for('screen_products'))

@app.route('/admin/delete_venproduct/<prodid>')
def delete_venproduct(prodid):
    id = session['admin']
    if id == None:
        return redirect(url_for('admin_login'))
    else:
        pdeet =Products.query.get_or_404(prodid)
        db.session.delete(pdeet)
        db.session.commit()
        flash('Vendor product deleted successfully')
        return redirect(url_for('screen_products'))



@app.route('/admin/services/',methods=["POST","GET"])
def services():
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        if request.method=="GET":
            data=db.session.query(Styles).order_by(Styles.style_id.desc()).all()    
            return render_template('admin/addservices.html',data=data)
        else:
            sname=request.form.get("stylename")
            if sname !="":
                sty=Styles(style_name=sname)
                db.session.add(sty)
                db.session.commit()
                flash("Service added successfully")
                return redirect(url_for('services'))
            else:
                return redirect(url_for('services'))

@app.route('/admin/services/editservice',methods=["POST", "GET"])
def editservice():
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        # retrieve and update, then return a feedback
        styleid = request.args.get('styleid')
        sname = request.args.get('stylename')
        edit = Styles.query.get(styleid)
        edit.style_name=sname
        db.session.commit()
        rsp = "Style updated successfully"
        return rsp

@app.route('/admin/services/delete/<id>')
def delete_services(id):
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        #retrieve the style as an object
        styobj=Styles.query.get_or_404(id)
        db.session.delete(styobj)
        db.session.commit()
        flash("Style Deleted Successfully")
        return redirect(url_for('services'))

@app.route('/admin/allcostumers')
def all_customers():
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        cust = Customers.query.order_by(Customers.cust_id.desc()).all()
        return render_template('admin/all_customers.html',cust=cust)

@app.route('/admin/product_category',methods=["POST","GET"])
def add_prodcategory():
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        if request.method=="GET":
            data=db.session.query(Category).order_by(Category.cat_id.desc()).all()
            return render_template('admin/add_productcategory.html',data=data)
        else:
            cat=request.form.get("catname")
            if cat != '':
                c=Category(cat_name=cat)
                db.session.add(c)
                db.session.commit()
                flash("Service added successfully")
                return redirect(url_for('add_prodcategory'))
            else:
                return redirect(url_for('add_prodcategory'))

@app.route('/admin/product_category/editcategory')
def editcategory():
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        # retrieve and update, then return a feedback
        catid = request.args.get('catid')
        cname = request.args.get('catname')
        edit = Category.query.get(catid)
        edit.cat_name=cname
        db.session.commit()
        rsp = "Category updated successfully"
        return rsp


@app.route('/admin/product_category/delete/<id>')
def delete_category(id):
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        #retrieve the cat as an object
        catobj=Category.query.get_or_404(id)
        db.session.delete(catobj)
        db.session.commit()
        flash("Category Deleted Successfully")
        return redirect(url_for('add_prodcategory'))

@app.route('/admin/contactus')
def contactus_rsp():
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        msgs = Messages.query.order_by(Messages.msg_date.desc()).all()
        return render_template('admin/contactus_msg.html',msgs=msgs)

@app.route('/admin/removed_services')
def removed_services():
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        stydeets = Ven_style.query.filter(Ven_style.venstyle_status=='remove').all()
        return render_template('admin/removed_services.html',stydeets=stydeets)
    
@app.route('/admin/removed_products')
def removed_products():
    if session.get('admin') ==None:
        return redirect(url_for('admin_login'))
    else:
        prodeets = Products.query.filter(Products.prod_status=='remove').all()
        return render_template('admin/removed_products.html', prodeets=prodeets)