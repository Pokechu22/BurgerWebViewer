from html import escape
from browser import document, window, html, ajax, webworker, console
from asyncio.futures import CancelledError
import traceback
import json
import sys

BURGER_DATA_PREFIX = "https://pokechu22.github.io/Burger/"

worker = None
active_future = None
def call_worker(message, data):
    global worker
    global active_future

    if not worker:
        document["vitrine-progress-label"].textContent = "Starting worker..."
        def progress_handler(message_name, message, src):
            data = message.data.to_dict()
            print("Progress update:", data)

            document["vitrine-progress-label"].textContent = data['desc']
            if 'value' in data:
                document["vitrine-progress"].max = data['max']
                document["vitrine-progress"].value = data['value']
            else:
                document["vitrine-progress"].removeAttribute('max')
                document["vitrine-progress"].removeAttribute('value')

        # Ugly hack to get an absolute URL from a relative one
        # https://stackoverflow.com/a/34020609/3991344
        url = html.A(href='worker.py').href
        worker = webworker.WorkerParent(url, sys.path, {"BURGER_DATA_PREFIX": BURGER_DATA_PREFIX}, brython_options={"debug": 1})
        worker.bind_message('progress', progress_handler)

    if active_future is not None:
        active_future.cancel()
        active_future = None

    active_future = worker.post_message(webworker.Message(message, data), want_reply=True)
    def callback(future):
        if active_future is not active_future:
            return

        active_future = None
        try:
            document.getElementById("vitrine").innerHTML = future.result().data.to_dict()['result']
            attach_tooltip_handlers()
        except CancelledError:
            pass
        except:
            traceback.print_exc()
            document.getElementById("vitrine").innerHTML = '<div class="entry"><h3>Error callback</h3><pre>' + escape(traceback.format_exc()) + '</pre></div>'
    active_future.add_done_callback(callback)

def update_result(*args, **kwargs):
    left = document.select("#version-main select")[0].value
    right = document.select("#version-diff select")[0].value
    document.select("#version-main span")[0].textContent = left
    document.select("#version-diff span")[0].textContent = right

    document.getElementById("vitrine").innerHTML = '''
    <h2>Working...</h2><div class="entry">
    <h3><label for="vitrine-progress" id="vitrine-progress-label">Loading burger JSONs...</label></h3>
    <progress id="vitrine-progress"></progress>
    </div>
    '''

    if left == "None" and right == "None":
        #window.location = "about"
        return
    elif left == "None":
        data = { "main": right }
        call_worker("vitrine", left)
    elif right == "None":
        data = { "main": left }
        call_worker("vitrine", data)
    else:
        data = { "main": left, "diff": right }
        call_worker("hamburglar", data)

document.select("#version-main select")[0].bind("change", update_result)
document.select("#version-diff select")[0].bind("change", update_result)

# Tooltips
tooltip = html.DIV(id="tooltip")
document.select("body")[0] <= tooltip
def mousemove(event):
    tooltip.style.top = str(event.pageY - 30) + "px"
    tooltip.style.left = str(event.pageX + 20) + "px"
document.bind("mousemove", mousemove)

def show_tooltip(event):
    tooltip.textContent = event.currentTarget.title
    tooltip.style.display = "block"

def hide_tooltip(event):
    tooltip.style.display = "none"

def attach_tooltip_handlers():
    for element in document.select(".item, .texture, .craftitem"):
        element.bind("mouseover", show_tooltip)
        element.bind("mouseout", hide_tooltip)

# Used by the sounds topping.
def playSound(element):
    link = element.dataset.link
    element.parentElement.innerHTML = "<audio autoplay controls><source src=\"" + link + "\" type=\"audio/ogg\" /></audio>"
window.playSound = playSound

def initalize(request):
    versions = json.loads(request.responseText)

    if len(versions) < 1:
        raise Exception("No versions are available")

    main = document.query.getfirst("main", None)
    if main not in versions:
        main = versions[0]

    diff = document.query.getfirst("diff", None)
    if diff not in versions:
        diff = "None"

    for ver in versions:
        document.select("#version-main select")[0] <= html.OPTION(ver, value=ver)
        document.select("#version-diff select")[0] <= html.OPTION(ver, value=ver)

    document.select("#version-main select")[0].disabled = False
    document.select("#version-main select")[0].value = main
    document.select("#version-diff select")[0].disabled = False
    document.select("#version-diff select")[0].value = diff

    update_result()

req = ajax.ajax()
req.open("GET", BURGER_DATA_PREFIX + "versions.json", True)
req.bind("complete", initalize)
req.send()