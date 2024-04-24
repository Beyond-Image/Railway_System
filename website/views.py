from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, session
from flask_login import login_required, current_user
from .models import Train, Seat, Ticket, User, Schedule
from . import db
from sqlalchemy import func
from datetime import datetime
from collections import defaultdict, Counter


def role_req(role):
    def decorator(f):
        def decorator_funct(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please Sign In To Access', category='error')
                return redirect(url_for('auth.login'))
            elif current_user.role != role:
                flash('Not Authorized To Access Page', category='error')
                return redirect(url_for('views.home'))
            return f(*args, **kwargs)
        return decorator_funct
    return decorator



views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template("home.html", user=current_user)

@views.route('/ticket', methods=['GET', 'POST'])
@login_required
def ticket():

    ticks = Ticket.query.filter_by(user_id=current_user.id).all()
    ticket_list = [tick.seat_id for tick in ticks]
    route_nums = [tick.route_id for tick in ticks]
    train_nums = [tick.train_id for tick in ticks]

    routes = Schedule.query.filter(Schedule.route_id.in_(route_nums)).all()
    trains = Train.query.filter(Train.train_id.in_(train_nums)).all()
    seats = Seat.query.filter(Seat.seat_id.in_(ticket_list)).all()

    tickets_by_train = defaultdict(list)
    for tick in ticks:
        tickets_by_train[tick.route_id].append(tick)


    action = request.form.get('action')

    if action == 'searchbtn':
        query = request.form.get('route_picker')
        if query != 'all':
            routes = Schedule.query.filter(Schedule.route_id==query).all()
            return render_template("ticket.html", user=current_user, trains=trains, tickets=ticks, tickets_by_train=tickets_by_train, seats=seats, routes=routes)
        else:
            routes = Schedule.query.filter(Schedule.route_id.in_(route_nums)).all()
            return render_template("ticket.html", user=current_user, trains=trains, tickets=ticks, tickets_by_train=tickets_by_train, seats=seats, routes=routes)



    if action == 'manage':
        ticket_ids = request.form.getlist('ticket_id')
        routenum = request.form.get('routenum')

        session['tick_id_list'] = ticket_ids
        session['routenum'] = routenum

        return redirect(url_for('views.cancel'))

    return render_template("ticket.html", user=current_user, trains=trains, tickets=ticks, tickets_by_train=tickets_by_train, seats=seats, routes=routes)




@views.route('/cancel', methods=['GET', 'POST'])
@login_required
def cancel():
    routenum = session['routenum']
    selected_tickets = session['tick_id_list']
    route = Schedule.query.filter(Schedule.route_id == routenum).first()
    ticks = Ticket.query.filter(Ticket.ticket_id.in_(selected_tickets)).all()
    seatnum = [ticket.seat_id for ticket in ticks if str(ticket.ticket_id) in selected_tickets]
    seats = Seat.query.filter(Seat.seat_id.in_(seatnum)).all()


    if request.method == 'POST':
        picked_tickets = request.form.getlist('canceler')
        print([picked_tickets])
        cancel_tickets = Ticket.query.filter(Ticket.seat_id.in_(picked_tickets)).all()
        cancel_seat = Seat.query.filter(Seat.seat_id.in_(picked_tickets))

        for ticket in cancel_tickets:
            print(ticket.ticketnum)
            ticket.purchased = 'no'
            ticket.user_id = None
            db.session.commit()
        
        for seat in cancel_seat:
            seat.reserved = False
            db.session.commit()

        route = Schedule.query.filter(Schedule.route_id == routenum).first()
        num_seat_rev = Seat.query.filter_by(route_id=ticket.route_id, reserved=True).count()
        route.current_number_passenger = num_seat_rev
        db.session.commit()
        flash('Successfully Canceled Ticket', category='sucesses')
        return redirect(url_for('views.home'))

    return render_template('cancel.html', user=current_user, route = route, tickets=ticks, seats=seats)




@views.route('/confirm_payment', methods=['GET', 'POST'])
@login_required
def confirm_payment():
    selected_seats = session['selected_seats']
    routenum = session['routenum']

    route = Schedule.query.filter(Schedule.route_id==routenum).first()
    trains = Train.query.filter(Train.train_id==route.train_id).first()
    seats = Seat.query.filter_by(route_id=routenum).all()
    tickets = Ticket.query.filter(Ticket.seat_id.in_(selected_seats)).all()
    seat_nums = [seat.seat_number for seat in seats if str(seat.seat_id) in selected_seats]


    if request.method == 'POST':
        redirect(url_for('views.home'))

    return render_template('confirm_payment.html', user=current_user, trains=trains, seats=seats, selected_seats=selected_seats, seat_nums=seat_nums, route=route)
    

@views.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    selected_seats = session['selected_seats']
    routenum = session['routenum']
    route = Schedule.query.filter(Schedule.route_id==routenum).first()
    trains = Train.query.filter(Train.train_id==route.train_id).first()
    seats = Seat.query.filter_by(route_id=routenum).all()
    tickets = Ticket.query.filter(Ticket.seat_id.in_(selected_seats)).all()
    seat_nums = [seat.seat_number for seat in seats if str(seat.seat_id) in selected_seats]
    print(selected_seats)

    if request.method == 'POST':
        for seat in seats:
            if str(seat.seat_id) in selected_seats:
                seat.reserved = True
                db.session.commit()
        for ticket in tickets:
            if str(ticket.seat_id) in selected_seats:
                ticket.purchased = 'yes'
                ticket.user_id = current_user.id
                db.session.commit()

        db.session.commit()

        num_seat_rev = Seat.query.filter_by(route_id=routenum, reserved=True).count()
        route.current_number_passenger = num_seat_rev
        db.session.commit()



        session['routenum'] = routenum
        session['selected_seats'] = selected_seats

        flash('Payment Successful', category='success')
        return redirect(url_for('views.confirm_payment'))

    return render_template('payment.html', user=current_user, trains=trains, seats=seats, selected_seats=selected_seats, tickets=tickets, seat_nums=seat_nums, route=route)

@views.route('/reserve/<routenum>', methods=['GET', 'POST'])
@login_required
def reserve(routenum):
    route = Schedule.query.filter(Schedule.route_id==routenum).first()
    trainnum = route.train_id
    trains = Train.query.filter(Train.train_id==trainnum).first()
    seats = Seat.query.filter_by(route_id=routenum).all()

    if request.method == 'POST':
        selected_seats = request.form.getlist('seat')
        session['routenum'] = routenum
        session['selected_seats'] = selected_seats
        return redirect(url_for('views.payment'))

    return render_template("reservation.html", user=current_user, trains=trains, seats=seats, route=route)

@views.route('/search', methods = ['GET', 'POST'])
@login_required
def search():
    trains = Train.query.all()
    action = request.form.get('action')
    searchbar = []

    if action == 'searchbtn':
        criteria = request.form.get('criteria')
        query = request.form.get('searchbar')

        if criteria == 'trainnum':
            routes = db.session.query(Schedule, Train).join(Schedule).filter(Schedule.train_id == query).all()
            print(routes)
        elif criteria == 'date':
            routes = db.session.query(Schedule, Train).join(Schedule).filter(Schedule.date == query).all()
        elif criteria == 'Destination':
            routes = db.session.query(Schedule, Train).join(Schedule).filter(Schedule.destination == query).all()
        elif criteria == 'departloc':
            routes = db.session.query(Schedule, Train).join(Schedule).filter(Schedule.depart_location == query).all()
        elif criteria == 'to-from':
            from_location, to_location = query.split('-')
            routes = db.session.query(Schedule, Train).join(Train).filter(Schedule.depart_location == from_location, Schedule.destination == to_location).all()
        else:
            routes = db.session.query(Schedule, Train).join(Train, Schedule.train_id == Train.train_id).all()

        return render_template("search.html", user=current_user, routes=routes, trains=trains)

    elif action == 'reserve':
        route_num = request.form.get('tracker')
        return redirect(url_for('views.reserve', routenum=route_num))
    
    routes = db.session.query(Schedule, Train).join(Train, Schedule.train_id==Train.train_id).all()

    return render_template("search.html", user=current_user, routes=routes, trains=trains)

@views.route('/addtrain', methods=['GET', 'POST'])
@role_req('admin')
def addtrain():

    if request.method == 'POST':
        capacity= request.form.get('capacity')

        new_train = Train(capacity=capacity)
        db.session.add(new_train)
        db.session.commit()


        flash('Train Successfully Added', category='success')
        return render_template("addtrain.html", user=current_user)

    return render_template("addtrain.html", user=current_user)

@views.route('/deltrain', methods=['GET', 'POST'])
@login_required
def deltrain():
    trains = Train.query.all()
    action = request.form.get('action')

    if action == "delete":
        train_id = request.form.get('trainnum')
        train = Train.query.filter_by(train_id=train_id).first()
        routes = Schedule.query.filter(Schedule.train_id == train_id).all()
        tickets = Ticket.query.filter(Ticket.train_id==train_id).all()
        seats = Seat.query.filter(Seat.train_id==train_id).all()


        if train:
            if tickets:
                for ticket in tickets:
                    db.session.delete(ticket)
                    db.session.commit()

            if seats:
                for seat in seats:
                    db.session.delete(seat)
                    db.session.commit()

            if routes:
                for route in routes:
                    db.session.delete(route)
                    db.session.commit()

            db.session.delete(train)
            db.session.commit()
            trains = Train.query.all()
            flash('Successfully Deleted Train', category='success')
            render_template('deltrain.html', user=current_user, trains=trains)

    elif action == 'searchbtn':
        criteria = request.form.get('criteria')
        query = request.form.get('searchbar')

        if criteria == 'all':
            trains = Train.query.all()

        if criteria == 'trainnum':
            trains = Train.query.filter(Train.train_id == query).all()

        if criteria == 'capacity':
            trains = Train.query.filter(Train.capacity==query).all()

        render_template('deltrain.html', user=current_user, trains=trains)
    

    return render_template("deltrain.html", user=current_user, trains=trains)



@views.route('/addroute', methods=['GET' ,'POST'])
@login_required
def addroute():
    trains = Train.query.all()

    if request.method == 'POST':
        trainnum = request.form.get('trainnum')
        depart_location = request.form.get('departloc')
        destination = request.form.get('destination')
        depart_time = request.form.get('departtime')
        arrival_time = request.form.get('arrivaltime')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        train = Train.query.filter_by(train_id=trainnum).first()

        new_route = Schedule(train_id=trainnum, depart_location=depart_location, destination=destination, depart_time=depart_time, arrival_time=arrival_time, date=date)
        db.session.add(new_route)
        db.session.commit()

        routenum = Schedule.query.filter_by(train_id=trainnum, depart_location=depart_location, destination=destination, depart_time=depart_time, arrival_time=arrival_time, date=date).first()

        for seat_num in range(1, int(train.capacity)+1):
            new_seat = Seat(train_id=trainnum, route_id=routenum.route_id, seat_number=seat_num)
            db.session.add(new_seat)
        db.session.commit()

        seats = Seat.query.filter_by(route_id=routenum.route_id).all()

        for seat in seats:
            new_ticket = Ticket(train_id=trainnum, user_id=None, seat_id=seat.seat_id, route_id=routenum.route_id)
            db.session.add(new_ticket)
            db.session.commit()


        flash('Route Successfully Added', category='success')
        return render_template('addroute.html', user=current_user, trains=trains)

    return render_template('addroute.html', user=current_user, trains=trains)


@views.route('/delroute', methods=['GET', 'POST'])
@login_required
def delroute():
    routes = Schedule.query.all()

    action = request.form.get('action')

    if action =='searchbtn':
        criteria = request.form.get('criteria')
        query = request.form.get('searchbar')

        if criteria == 'routenum':
            routes = Schedule.query.filter(Schedule.route_id==query).all()
        elif criteria == 'date':
            routes = Schedule.query.filter(Schedule.date == query).all()
        elif criteria == 'Destination':
            routes = Schedule.query.filter(Schedule.destination == query).all()
        elif criteria == 'departloc':
            routes = Schedule.query.filter(Schedule.depart_location == query).all()
        else:
            routes = Schedule.query.all()

        return render_template("delroute.html", user=current_user, routes=routes)

    elif action == 'cancel':
        routenum = request.form.get('routenum')
        route = Schedule.query.filter(Schedule.route_id == routenum).first()
        seats = Seat.query.filter(Seat.route_id==route.route_id).all()
        tickets = Ticket.query.filter(Ticket.route_id==route.route_id).all()

        for seat in seats:
            db.session.delete(seat)
            db.session.commit()

        for ticket in tickets:
            db.session.delete(ticket)
            db.session.commit()

        db.session.delete(route)
        db.session.commit()

        routes= Schedule.query.all()
        flash('Successfully Deleted Route', category='success')
        return render_template('delroute.html', user=current_user, routes=routes)
    return render_template('delroute.html', user=current_user, routes=routes)


@views.route('/admin/tickets', methods=['GET', 'POST'])
@login_required
def admin_tickets():
    if current_user.role != 'admin':
        return redirect(url_for('views.home'))
    
    users = User.query.all()
    tickets = Ticket.query.all()
    routes = Schedule.query.all()
    trains = Train.query.all()
    seats = Seat.query.all()
   
    
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'filter':
            user_id = request.form.get('user_pick')
            
            if user_id == 'all':
                users = User.query.all()
            else:
                users = User.query.filter(User.id==user_id).all()
            return render_template('admin_tickets.html', user=current_user, tickets=tickets, all_users=users, trains=trains, seats=seats, routes=routes)

        if action == 'remove':
            ticket_id = request.form.get('ticket_id')

            tick = Ticket.query.get(ticket_id)
            seat = Seat.query.get(tick.seat_id)
            route = Schedule.query.get(tick.route_id)
            train = Train.query.get(tick.train_id)

            seat.reserved = False
            tick.purchased = 'no'
            tick.user_id = None

            num_seat_rev = Seat.query.filter_by(train_id=train.train_id, reserved=True).count()
            route.curr_num_pass = num_seat_rev

            db.session.commit()
            return render_template('admin_tickets.html', user=current_user, tickets=tickets, all_users=users, trains=trains, seats=seats, routes=routes)
            
        elif action == 'add':
            user_id = request.form.get('user_id')
            routenum = request.form.get('routenum')
            session['selected_user'] = user_id

            return redirect(url_for('views.admin_reserve', routenum=routenum))
 
    return render_template('admin_tickets.html', user=current_user, tickets=tickets, all_users=users, trains=trains, seats=seats, routes=routes)


@views.route('/admin/reserve/<routenum>', methods=['GET', 'POST'])
@login_required
def admin_reserve(routenum):
    if current_user.role != 'admin':
        return redirect(url_for('views.home'))
    
    routes = Schedule.query.filter(Schedule.route_id==routenum).first()
    seats = Seat.query.filter_by(route_id=routes.route_id).all()
    selected_user = session['selected_user']

    if request.method == 'POST':
        selected_seats = request.form.getlist('seat')
        session['routenum'] = routenum
        session['selected_seats'] = selected_seats
        print(selected_seats)
        session['selected_user'] = selected_user
        return redirect(url_for('views.admin_ticket_confirm'))

    return render_template('admin_seat.html', user=current_user, routes=routes, seats=seats, selected_user=selected_user)

@views.route('admin/ticket/confirm', methods=['GET', 'POST'])
@login_required
def admin_ticket_confirm():
    routenum = session['routenum']
    selected_seats = session['selected_seats']
    selected_user = session['selected_user']

    routes = Schedule.query.filter(Schedule.route_id==routenum).first()
    seats = Seat.query.filter_by(route_id=routenum).all()
    tickets = Ticket.query.filter(Ticket.seat_id.in_(selected_seats)).all()
    selected_user_entity = User.query.filter(User.id==selected_user).first()
    seat_nums = [seat.seat_number for seat in seats if str(seat.seat_id) in selected_seats]

    if request.method == 'POST':
        for seat in seats:
            if str(seat.seat_id) in selected_seats:
                seat.reserved = True
                db.session.commit()
        for ticket in tickets:
            if str(ticket.seat_id) in selected_seats:
                ticket.purchased = 'promo'
                ticket.user_id = selected_user
                db.session.commit()
        db.session.commit()
        num_seat_rev = Seat.query.filter_by(route_id=routes.route_id, reserved=True).count()
        routes.current_number_passenger = num_seat_rev
        db.session.commit()

        flash('Customers Successfully Given Tickets', category='success')
        return redirect(url_for('views.home'))

    return render_template('admin_ticket_confirm.html', user=current_user, routes=routes, seats=seats, selected_seats=selected_seats, tickets=tickets, seat_nums=seat_nums, selected_user_entity=selected_user_entity)

@views.route('admin/report', methods=['GET', 'POST'])
@login_required
def admin_report():
    if current_user.role != 'admin':
        return redirect(url_for('views.home'))
    
    routes = Schedule.query.all()
    info = []
    action = request.form.get('action')

    if action == 'searchbtn':
        criteria = request.form.get('criteria')
        query = request.form.get('searchbar')
        if criteria == 'routenum':
            routes = Schedule.query.filter(Schedule.route_id==query).all()
        if criteria == 'all':
            routes = Schedule.query.all()
        pass

    for route in routes:
        num_tickets_sold = Ticket.query.filter(Ticket.route_id==route.route_id, Ticket.purchased=='yes').count()
        num_tickets_promoed = Ticket.query.filter(Ticket.route_id==route.route_id, Ticket.purchased=='promo').count()
        seats_taken = route.current_number_passenger
        tickets = Ticket.query.filter(Ticket.route_id==route.route_id, Ticket.purchased != 'no').all()

        demographics = {}

        for ticket in tickets:
            person = User.query.filter(User.id==ticket.user_id).first()
            ethnicity = person.ethnicity
            if ethnicity in demographics:
                demographics[ethnicity] += 1
            else:
                demographics[ethnicity] = 1

        print(demographics)

        info.append({
            'route': route,
            'num_sold': num_tickets_sold,
            'num_promo': num_tickets_promoed,
            'num_seats_taken': seats_taken,
            'demographics': demographics    
        })

    return render_template('report.html', user=current_user, info=info)

@views.route('profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@views.route('base')
@login_required
def base():
    return render_template('base.html', user=current_user)