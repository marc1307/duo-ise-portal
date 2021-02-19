// Const
const api_requestAccess = '/api/requestAccess'

// Globals

// Functions
function requestAccess(e) {
    qs = getQueryParams(window.location.search)
    sessionId = qs["sessionId"]
    host = $('#host')[0].value
    console.log("SessionID: "+sessionId)
    console.log("Host: "+host)

    url = api_requestAccess
    $.ajax({
        url: url,
        method: "POST",
        data: { sessionId: sessionId, host: host },
        error: function(xhr, textStatus, error) {
            alert(xhr.textStatus)
        }
    }).done(
        function(data) {
            alert(data)
        }
    )
}


// onLoad
$(document).ready(
    function() {
        console.log("rdy")
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