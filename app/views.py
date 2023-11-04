from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, auth
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .resp import r500,r200
from .models import Profile,EventTable,Event
from userapi import settings
from .tokens import generate_token
from django.core.mail import EmailMessage, send_mail
# Create your views here.

def home(request):
    return HttpResponse('This is the homepage!')

@api_view(['POST'])
def signup(request):
    if request.method == 'POST':
        data = request.data
        username = data['username'].strip()
        email = data['email']
        pass1 = data['password']
        phone = data['phone']
        college = data['college']
        year = data['year']
        # print(username, email, pass1, pass2)
        # checks for same username
        # if User.objects.filter(username=username).first():
        #     return Response(
        #         {'status': 404,
        #             "registered": False,
        #             'message': "Username already registered",
        #             "username": username
        #             }
        #     )

        # checks if the username exists
        if User.objects.filter(email=email).first():
            return Response({
                'status': 404,
                "registered": False,
                'message': "Email already registered",
                "username": username
            })

        # Creates a new user and adds it to the profile with a new CA_code
        else:
            new_user = User.objects.create_user(username, email, pass1)

            # Not activating the user unless the confirmation mail is opened
            new_user.is_active = False
            new_user.save()

            ca_profile = Profile.objects.create(userId=new_user.id,username=username, email=email, phone=phone, college=college, year=year)
            ca_code = ca_profile.CA
            ca_profile.save()

            # Confimation link mail
            current_site = get_current_site(request)
            email_subject = "Petrichor Fest - Campus Ambassador Programme Confirmation"
            confirmation_message = render_to_string('confirmation_email.html',
                                                    {
                                                        'username': username,
                                                        'domain': current_site.domain,
                                                        'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
                                                        'token': generate_token.make_token(new_user)
                                                    })   # add a html template
            email_cnf = EmailMessage(
                email_subject,
                confirmation_message,
                settings.EMAIL_HOST_USER,
                [new_user.email],
            )
            email_cnf.fail_silently = False
            print(settings.EMAIL_BACKEND, "a")
            email_cnf.send()
            print("mail sent to", new_user.email)

            # Sending Email with CA code



            return Response({
                'status': 200,
                "registered": "true",
                'message': "Success",
                "username": username
            })

@api_view(['POST'])
def user_login(request):
    if request.method == 'POST':

        if request.data is None:
            return r500("invalid form")
        data=request.data

        username = data['username'].strip()
        password = data['password']
        my_user = authenticate(username = username, password = password)
        if my_user is not None:
            login(request, my_user)
            profile = Profile.objects.get(email=username)
            return Response({
                "ok": "true",
                "CA": profile.CA,
                "username": profile.username,
                "registrations": 0
            })
        return Response({
            "message": "The username or password is incorrect",
            "logged-in": "false"
        })

@api_view(['POST'])
def user_logout(request):
    logout(request)
    return Response(
        {
            "logged-in": "false",
            "message": "User has logged out"
        }
    )
    # return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        new_user = User.objects.get(pk=uid)
        # print(new_user.username)
        # print(uid)
        # print(token)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        new_user = None

    if new_user is not None and generate_token.check_token(new_user, token):

        new_user.is_active = True
        new_user.save()
        userprof = Profile.objects.get(email=new_user.username)
        userprof.generate_CA()
        # print(userprof.CA)
        userprof.save()
        login(request, new_user)
        subject = "Welcome to Petrichor's Campus Ambassador Programme"
        message = f"Hello there, {new_user.username} \nPlease click the following link to activate your CA account {userprof.CA}"
        from_mail = settings.EMAIL_HOST_USER
        to_mail_ls = [new_user.email]

        send_mail(subject, message, from_mail, to_mail_ls, fail_silently=True)
        # return Response(
        #     {
        #         "logged-in": "True",
        #         "message": "Your email has been confirmed"
        #     }
        # )
        return render(request, 'success.html')
    else:
        # return Response(
        #     {
        #         "logged-in": "False",
        #         "message": "Account was not verified, activation failed"
        #     }
        # )
        return redirect(request, 'failure.html')


def mailtest(request):
    current_site = get_current_site(request)
    email_subject = "Petrichor Fest - Campus Ambassador Programme Confirmation"
    confirmation_message = render_to_string('confirmation_email.html',
                                            {
                                                'username': 'hello',
                                                'domain': current_site.domain,
                                                'uid': "urlsafe_base64_encode(force_bytes('new_user.pk'))",
                                                'token': "generate_token.make_token('new_user')"
                                            })   # add a html template
    email_cnf = EmailMessage(
        email_subject,
        confirmation_message,
        settings.EMAIL_HOST_USER,
        ['112201015@smail.iitpkd.ac.in'],
    )
    print(email_cnf)
    email_cnf.fail_silently = False
    # print(settings.EMAIL_BACKEND, "a")
    email_cnf.send()
    print('email sent to', '112201015@smail.iitpkd.ac.in')

    return HttpResponse("email send to")

@api_view(['POST'])
def apply_event(request):

    if request.data is None:
        return r500("invalid form")
    data=request.data

    try:
        user_id=data['userid']
        event_id=data['eventId'].strip()
        ca_code=data['ca'].strip()
        transactionId=data['transactionId'].strip()

    except KeyError:
        return r500("userid, eventid, and cacode required. send all. if cacode is not there send empty string'")
# try:
    email=Profile.objects.get(userId=user_id).email
    verified=False
    if(email.endswith("smail.iitpkd.ac.in")):
        verified=True
        transactionId="Internal Student"
    print("here")
    eventTableObject = EventTable.objects.create(eventId=event_id,user_id=user_id,ca_code=ca_code,transactionId=transactionId,verified=verified)
    eventTableObject.save()
    return r200("Event applied")
    # except Exception:
    #     print(user_id,event_id,transactionId,ca_code,verified)
    #     return r500("Oopsie Doopsie")
    
@api_view(['GET'])
def getUnconfirmed(request):
    try:
        unconfirmed_users=set(EventTable.objects.exclude(transactionId="Internal Student").values_list('user_id'))
        print(unconfirmed_users)
        unconfirmed_list=[]
        for user in unconfirmed_users:
            user_id=user[0]

            events=EventTable.objects.filter(user_id=user_id)
            event_dict=dict()
            for event in events:
                if not event.verified:
                    event_dict[Event.objects.get(eventId=event.eventId).name]=event.transactionId
            
            user_name=Profile.objects.get(userId=user_id).username
            unconfirmed_list.append({user_name:event_dict})
        
        return Response(
            {
                "data":unconfirmed_list
            }
        )
    except Exception as e:
        return r500("Oopsie Doopsie")
    
@api_view(['GET'])
def getEventUsers(request):
    if request.method == "GET":
        events=[]
        try:
            allEvents=Event.objects.all()
            for event in allEvents:
                participantsId=set(EventTable.objects.filter(eventId=event.eventId).values_list('user_id'))
                participants=[]
                for id in participantsId:
                    user=Profile.objects.get(userId=id[0])
                    participants.append({
                        "name":user.username,
                        "email":user.email,
                        "phone":user.phone,
                        "CA":user.CA
                    })
                events.append({
                    "name": event.name,
                    "participants":participants
                })


            print("Coreect")
            return Response({
                'status': 200,
                'data':["name","email","phone","CA"],
                "events":events
            })
        except Exception as e:
            return r500("Opps!! Unable to complete the request!!!")
    
@api_view(['POST'])
def verifyCA(request):
    try:
        if request.data == None:
            return r500("Invalid Form")
        
        data=request.data

        inputCAcode=data['CA_code'].strip()
        try:
            event=EventTable.objects.get(ca_code=inputCAcode)
            return Response({
                'status' : 200,
                'verified': True
            })
        except Exception as e:
            return Response({
                'status':404,
                'verified': False,
                'msg':"Not found in our db"
            })




    except Exception as e:
        return Response({
                'status':400,
                'verified': False,
                'msg':"Opps!! Unable to complete the request!!!"
            })
    