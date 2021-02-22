// Const
const api_requestAccess         = '/api/requestAccess'
const api_requestAccessPasscode = '/api/requestAccessPasscode'

// Globals

// Functions
function requestAccess(e) {
    qs = getQueryParams(window.location.search)
    sessionId = qs["sessionId"]
    host = $('#host')[0].value
    console.log("SessionID: "+sessionId)
    console.log("Host: "+host)

    url = api_requestAccess
    if (window.location.protocol !== "file:") {
        $("#authres1").text("Please wait for approval...")
        $.ajax({
            url: url,
            method: "POST",
            data: { sessionId: sessionId, host: host },
            error: function(xhr, textStatus, error) {
                console.log(xhr.textStatus)
            }
        }).done(
            function(data) {
                console.log(data)
                if (data.success) {
                    $("#authProgress").css("background-color", "green")
                } else {
                    $("#authProgress").css("background-color", "red")
                    $("#authres1").text(data.error)
                }
            }
        )
    } else {
        console.log("Warning Protocol file:")
    }
}


// onLoad
$(document).ready(
    function() {
        console.log("document.ready")
        if (window.location.protocol !== "file:") {
            var intervall_getStatus = setInterval(function() {
                $.ajax({
                    url: "/api/status",
                    error: function(xhr, textStatus, error) {
                        console.log(xhr.textStatus)
                    }
                }).done(
                    function (data) {
                        if(data.success) {
                            if (data.data.ISE !== false) {
                                $("#mac").text(data.data.ISE.mac)
                                $("#ip4").text(data.data.ISE.framed_ip_address)
                            }

                            if (data.data.PreAuth !== false) {
                                if (data.data.PreAuth.success) {
                                    $("#authres1").text("Found Device: "+data.data.PreAuth.DeviceName)
                                } else {
                                    $("#authres1").text(data.data.PreAuth.msg)
                                    $("#authProgress").css("background-color", "red")
                                }
                            }

                            if (data.data.Auth !== false) {
                                if (data.data.Auth.success) {
                                    $("#authres2").text("Sent Push successfully")
                                }
                            }

                            if (data.data.AuthStatus !== false) {
                                if(data.data.AuthStatus.success) {
                                    $("#authres3").text(data.data.AuthStatus.msg)
                                    $("#authProgress").css("background-color", "green")
                                } else {
                                    $("#authres3").text(data.data.AuthStatus.msg)
                                    $("#authProgress").css("background-color", "red")
                                }
                            }

                            // Redirect Client if CoA is sent to NAD
                            if (data.data.detail.IseCoaSent) {
                                $("#authres4").text("Guest Access approved. Please wait")
                                setTimeout(function() {
                                    followRedirect()
                                }, 1500)
                            }
                        }

                        $('#status').text(data.status)
                        $('pre#detail').text(JSON.stringify(data.detail, undefined, 2))
                    }
                )
            }, 1000)
        }


        // redirect
        qs = getQueryParams(window.location.search)
        $('a#redirect').attr("href", qs["redirect_url"])

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