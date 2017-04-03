from django.shortcuts import render, HttpResponse, HttpResponseRedirect
import requests
import digitalocean
import json
import twilio.twiml
from .models import User
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from twilio.rest import TwilioRestClient

# Create your views here.
ACCOUNT_SID = "add your account SID here"
AUTH_TOKEN = "add your auth token here"

def get_message(request):
    msg_from = request.GET.get('From')
    msg_body = request.GET.get('Body')
    body = msg_body.split(' ')
    print body[0].lower()
    if body[0].lower() == 'register':
        register(body[1], body[2], msg_from)
    elif body[0].lower() == 'get_link':
        linkauth(body[1], msg_from)
    elif body[0].lower() == 'droplets_list':
        print "abc"
        if is_registered(msg_from):
            all_droplets(msg_from)
            print "registered"
        else:
            resp = twilio.twiml.Response()
            resp.message("You have to register first by sending register your_email your_password")
    elif body[0].lower() == 'poweroff':
        power("power_off", msg_from, body[1])
    elif body[0].lower() == 'poweron':
        power("power_on", msg_from, body[1])
    elif body[0].lower()=="help_droplet" and is_registered(msg_from):
        help_droplet(msg_from)
    elif body[0].lower()=="create_droplet" and is_registered(msg_from):
        create_droplet(msg_from,body[1],body[2],body[3],body[4])
    elif body[0].lower()=="delete_droplet" and is_registered(msg_from):
        delete_droplet(msg_from,body[1])
    elif body[0].lower()=="resize_droplet" and is_registered(msg_from):
        print "resizing"
        resize_droplet(msg_from,body[1],body[2])
    return HttpResponse('done')


def all_droplets(phone):
    print phone
    user=User.objects.get(phone=phone)
    headers = {'Content-Type': 'application/json'}
    headers['Authorization'] = 'Bearer %s' %user.token

    r = requests.get('https://api.digitalocean.com/v2/droplets', headers=headers)
    res = json.loads(r.text)
    droplets=res['droplets']
    msg = ''

    for d in droplets:
        d_id = str(d['id'])
        name = str(d['name'])
        memory = str(d['memory'])
        cvpus = str(d['vcpus'])
        disk = str(d['disk'])
        locked = str(d['locked'])
        status = str(d['status'])
        date = str(d['created_at'])
        img_id = str(d['image']['id'])
        slug = str(d['image']['slug'])
        price_mon = str(d['size']['price_monthly'])
        price_hour = str(d['size']['price_hourly'])
        region = str(d['region']['name'])

        msg += "droplet id : " + d_id + '\n' + \
                "droplet name : " + name + '\n' + \
                "droplet memory : " + memory + '\n' + \
                "cpu : " + cvpus + '\n' + \
                "disk size : " + disk + '\n' + \
                "locked : " + locked + '\n' + \
                "status : " + status + '\n' + \
                "creation date : " + date + '\n' + \
                "image id : " + img_id + '\n' + \
                "slug : " + slug + '\n' + \
                "monthly price : " + price_mon + '\n' + \
                "hourly price : " + price_hour + '\n' + \
                "droplet region : " + region + '\n' + \
                '\n\n'


        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(
                to=phone,
               from_="+16202773118",
              body=msg,
        )

def get_code(request):
    code=request.GET.get('code')
    url="https://cloud.digitalocean.com/v1/oauth/token?client_id=ecf52935c659f9905bff80008805b206a4b3e51cbe78a1dfc68b368498cb17c5&client_secret=ab6b38f3fedbaf325935f7b32d39776d5cb4b06dd703ae6035aa47c12216a7fd&grant_type=authorization_code&code="+code+"&scope=read write&redirect_uri=http://dbbd94bb.ngrok.io/callback"
    r=requests.post(url)
    res=r.text
    ##saving token
    print res
    resp = json.loads(res)
    email = resp['info']['email']
    token = resp['access_token']
    user = User.objects.get(email=email)

    if is_registered(user.phone):
        user.token = token
        user.save()

        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(
        to=user.phone,
        from_="+16202773118",
        body="registered",
        )

    return HttpResponse(json.dumps(res))


def get_url(request):
    link = "https://cloud.digitalocean.com/v1/oauth/authorize?client_id=ecf52935c659f9905bff80008805b206a4b3e51cbe78a1dfc68b368498cb17c5&redirect_uri=http://dbbd94bb.ngrok.io/callback&response_type=code&scope=read write"
    return HttpResponseRedirect(link)

def linkauth(email, phone):
    if is_registered(phone):
        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
        print 'is registered'
        client.messages.create(
            to=phone,
            from_="+16202773118",
            body="You are already registered",
            )
    else:
        link = 'http://dbbd94bb.ngrok.io/get_url/'
        user = User(email=email, phone=phone)
        user.save()
        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
        print 'current phone %s' %phone
        client.messages.create(
            to=phone,
            from_="+16202773118",
            body=link,
            )

def delete_droplet(phone,id):
    user=User.objects.get(phone=phone)
    headers = {'Content-Type': 'application/json'}
    headers['Authorization'] = 'Bearer %s' %user.token

    r = requests.delete('https://api.digitalocean.com/v2/droplets/'+id+"/", headers=headers)
    res = json.loads(r.text)
    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
    client.messages.create(
    to=phone,
    from_="+16202773118",
    body="Droplet deleted",
    )

def resize_droplet(phone,id,size):
    user=User.objects.get(phone=phone)
    headers = {'Content-Type': 'application/json'}
    headers['Authorization'] = 'Bearer %s' %user.token
    # data={"type":"resize","size":size}
    print ({"type":"resize","size":size})
    r = requests.post('https://api.digitalocean.com/v2/droplets/'+id+"/actions", json={"type":"resize","size":size},headers=headers)
    res = json.loads(r.text)
    print r.text
    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
    client.messages.create(
    to=phone,
    from_="+16202773118",
    body="Droplet resize",
    )

def is_registered(phone):
    try:
        print phone
        user=User.objects.get(phone=phone)

        print "true"
        return True
    except User.DoesNotExist:
        return False

def get_machine_list():
    list=["ubuntu-14-04-x64","ubuntu-16-04-1-x64"]
    return list

def  get_region_list():
    return ["nyc1","sfo1","nyc2"]

def get_size_list():
    return ["512mb","1gb","2gb"]

def help_droplet(phone):
    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
    machine="Machines:\n"
    for m in get_machine_list():
        machine+="\t"+m

    regions="Regions:\n"
    for m in get_region_list():
        regions+="\t"+m

    size="Sizes:\n"
    for m in get_size_list():
        size+="\t"+m
    client.messages.create(
    to=phone,
    from_="+16202773118",
    body=machine+"\n"+regions+"\n"+size,
    )

def create_droplet(phone,name,image,region,size):
    user=User.objects.get(phone=phone)
    print phone,name,image,region,size
    headers = {'Content-Type': 'application/json'}
    headers['Authorization'] = 'Bearer %s' %user.token
    data='{"name":"'+name+'","region":"'+region+'","size":"'+size+'","image":"'+image+'","ssh_keys":null,"backups":false,"ipv6":true,"user_data":null,"private_networking":null,"volumes": null,"tags":["web"]}'
    print data
    r = requests.post('https://api.digitalocean.com/v2/droplets',data=str(data), headers=headers)
    res = json.loads(r.text)
    print r.text
    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
    client.messages.create(
    to=phone,
    from_="+16202773118",
    body="Droplet created",
    )

def register(email, password, phone):
    if is_registered(phone):
        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(
            to=phone,
            from_="+16202773118",
            body="You are already registered",
        )
    else:
        user = User(email=email, password=password, phone=phone)
        user.save()
        oauth(email, password)


def oauth(email,passw):
    print(email + passw)
    driver=webdriver.Chrome('/home/rajdeep1008/Desktop/chromedriver')

    driver.get('https://cloud.digitalocean.com/v1/oauth/authorize?client_id=ecf52935c659f9905bff80008805b206a4b3e51cbe78a1dfc68b368498cb17c5&redirect_uri=http://dbbd94bb.ngrok.io/callback&response_type=code&scope=read write')
    time.sleep(5)
    name=driver.find_element_by_name('user[email]')
    name.send_keys(email)
    passwo=driver.find_element_by_name('user[password]')
    passwo.send_keys(passw)
    name.submit()
    time.sleep(5)
    box=driver.find_element_by_id('ember975')
    hov = ActionChains(driver).move_to_element(box).click()
    hov.perform()

    btn=driver.find_element_by_name('client_id')
    btn.submit()


def power(req_type, msg_from, d_id):
    print(req_type + " " + d_id)
    if is_registered(msg_from):
        user = User.objects.get(phone=msg_from)
        headers = {'Content-Type': 'application/json'}
        headers['Authorization'] = 'Bearer %s' %user.token

        r = requests.post('https://api.digitalocean.com/v2/droplets/'+d_id+'/actions', json={"type": req_type}, headers=headers)
        res = json.loads(r.text)
        print(res)
    else:
        user = User.objects.get(phone=msg_from)
        phone = user.phone
        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(
            to=phone,
            from_="+16202773118",
            body="You are not registered",
            )
