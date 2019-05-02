WELCOME_MESSAGE = {
    "attachment":{
        "type":"template",
        "payload":{
            "template_type":"generic",
            "elements":[
                {
                    "title":"Welcome! to HOPSCOTCH HEALTH",
                    "image_url":"http://www.hopscotch.health/wp-content/uploads/2018/06/banner.png",
                    "subtitle":"We are a 'Digital Nutrition Care Team'",
                    "default_action": {
                        "type": "web_url",
                        "url": "http://www.hopscotch.health/wp-content/uploads/2018/06/banner.png",
                        "webview_height_ratio": "tall",
                    },
                    "buttons":[
                        {
                            "type":"web_url",
                            "url":"https://www.hello.hopscotch.health/testimonials",
                            "title":"Diet | Hopscotch Health | India"
                        },{
                            "type":"postback",
                            "title":"Let's get started",
                            "payload":"DEVELOPER_DEFINED_PAYLOAD"
                        }
                    ]
                }
            ]
        }
    }
}


PAYMENT_MESSAGE = {
    "attachment": {
        "type": "template",
        "payload": {
            "template_type": "generic",
            "elements": [
                {
                    "title": "Thank you for joining Hopscotch Health!",
                    "image_url": "http://www.logosvectorfree.com/wp-content/uploads/2017/12/vector-logo-of-the-Paytm-brand.jpg",
                    "subtitle": "We are a 'Digital Nutrition Care Team' where you communicate one on one with our nutritionist through WhatsApp. We focus on improving wellness for everyone. Our goal is to provide amazing patient focus care for everyone everyday.",
                    "default_action": {
                        "type": "web_url",
                        "url": "https://p-y.tm/j-tefid",
                        "webview_height_ratio": "tall",
                    },
                    "buttons": [
                        {
                            "type": "web_url",
                            "url": "https://p-y.tm/j-tefid",
                            "title": "Make Payment"
                        }, {
                            "type": "postback",
                            "title": "Let us know better!",
                            "payload": "DEVELOPER_DEFINED_PAYLOAD"
                        }
                    ]
                }
            ]
        }
    }
}
