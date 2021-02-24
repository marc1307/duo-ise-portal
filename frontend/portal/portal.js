// Const
const api_requestAccess         = '/api/requestAccess'
const api_requestAccessPasscode = '/api/requestAccessPasscode'

// Globals
qs = getQueryParams(window.location.search)

// Functions
function requestAccess(e) {
    
    sessionId = qs["sessionId"]
    host = $('#host')[0].value
    console.log("SessionID: "+sessionId)
    console.log("Host: "+host)

    socket.emit('auth', host)
}


// onLoad
$(document).ready(
    function() {
        console.log("document.ready")
        if (window.location.protocol !== "file:") {
            var socket = io.connect(window.location.protocol + "//" + document.domain + ':' + location.port);

            socket.on('connect', function(msg) {
                console.log("Socket connected")
            })

            socket.on('disconnect', (reason) => {
                console.log("Socket disconnected ("+reason+")")
            })
        }

        var $submit = $('#host_submit')

        // Toggle Passcode Field
        $('#usePasscode').on('click', function() {
            $('div#tokenform').slideToggle()
        }) 

        // Redirect
        qs = getQueryParams(window.location.search)
        $('a#redirect').attr("href", qs["redirect_url"])

        // Init: give ISE a little bit of time to send session to mnt node
        setTimeout(function() {
            sessionId = qs["sessionId"]
            socket.emit('init', sessionId)
        }, 1500)

        // Listen for Status Events
        socket.on('init', function(msg) {
            console.log(msg)
            debuglog(msg, " INIT")

            if (msg.IseSessionFound) {
                $submit.prop('disabled', false)
            }
        })

        // Listen for auth Events
        socket.on('auth', function(msg) {
            console.log(msg)
            debuglog(msg, " AUTH")

            if (msg.module === "preauth") {
                if (msg.success) {
                    if (msg.count.phone > 0) {
                        $("#authres1").text("Please wait")
                    } else {
                        $("#authres1").text("Please enter passcode below:")
                    }
                    $('input#passcode').val("")
                    $('#passcodeSection').slideDown()
                } else {
                    $("#authres1").text(msg.msg)
                    $("#authProgress").css("background-color", "red")
                    $submit.prop('disabled', false)
                }
            }

            if (msg.module === "preauth2") {
                if (msg.success) {
                    $("#authres2").text("Sending request to "+msg.device)
                }
            }

            if (msg.module === "auth") {
                if (msg.success) {
                    $("#authres3").text("Request sent")
                } else {
                    $("#authres3").text("Request could not be sent")
                    $("#authProgress").css("background-color", "red")
                    $submit.prop('disabled', false)
                }
            }

            if (msg.module === "auth_status") {
                if (msg.success) {
                    $("#authres3").text("Current status: "+msg.state)
                    if (msg.state === "allow") {
                        $("#authProgress").css("background-color", "green")
                        $("#authres5").text("=> Approved: Please wait for redirection :)")
                    }
                    if (msg.state === "deny") {
                        $("#authProgress").css("background-color", "red")
                        $("#authres5").text("=> "+msg.msg)
                        $submit.prop('disabled', false)
                    }
                } else {
                    $("#authres3").text("ERROR auth_status")
                    $("#authProgress").css("background-color", "red")
                    $submit.prop('disabled', false)
                }
            }

            if (msg.module === "ise-coa" && msg.success) {
                setTimeout(function() {
                    followRedirect()
                }, 1250)
            }
        })

        // Auth Requst
        $('#authRequest').submit(function( event ) {
            event.preventDefault();
            $submit.prop('disabled', true)
            sessionId = qs["sessionId"]
            host = $('input#host')[0].value
            $("#authProgress").css("background-color", "")
            $("span.authres").text("")
            console.log("SessionID: "+sessionId)
            console.log("Host: "+host)
            socket.emit('auth', host)
        })

        // Auth Request Passcode
        $('#passcodeRequest').submit(function( event ) {
            event.preventDefault();
            passcode = $('input#passcode')[0].value
            console.log("Passcode: "+passcode)
            socket.emit('auth_passcode', passcode)
        })


        // listen for debug messages
        socket.on('debug', function(msg) {
            console.log(msg)
            debuglog(msg, "DEBUG")
        })
    }
)



// Stuff
function getQueryParams(qs) {
    qs = qs.split('+').join(' ');

    var params = {},
        tokens,
        re = /[?&]?([^=]+)=([^&]*)/g;

    while (tokens = re.exec(qs)) {
        params[decodeURIComponent(tokens[1])] = decodeURIComponent(tokens[2]);
    }

    return params;
}

function followRedirect() {
    qs = getQueryParams(window.location.search)
    window.location.href = qs['redirect_url']
}

function debuglog(text, slug="") {
    $target = $('textarea#debug')

    if (slug !== "") {
        slug = slug+": "
    }
    
    $target.val(function(index, old) { return slug+JSON.stringify(text) + "\n" + old })
}