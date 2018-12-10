from html import escape
from browser import document, window, html, ajax, webworker, console
from asyncio.futures import CancelledError
import traceback
import json
import sys
worker = None
active_future = None

BURGER_DATA_PREFIX = "https://pokechu22.github.io/Burger/"

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
    progress_label = document.getElementById("vitrine-progress-label")
    progress_bar = document.getElementById("vitrine-progress") # starts in indeterminate state

    def updates_vitrine(f):
        global worker

        if not worker:
            progress_label.textContent = "Starting worker..."
            def progress_handler(message_name, message, src):
                data = message.data.to_dict()
                print("Progress update:", data)

                progress_label.textContent = data['desc']
                if 'value' in data:
                    progress_bar.max = data['max']
                    progress_bar.value = data['value']
                else:
                    progress_bar.removeAttribute('max')
                    progress_bar.removeAttribute('value')

            # Ugly hack to get an absolute URL from a relative one
            # https://stackoverflow.com/a/34020609/3991344
            url = html.A(href='worker.py').href
            worker = webworker.WorkerParent(url, sys.path)
            worker.bind_message('progress', progress_handler)

        """
        Decorator to update vitrine based on the future returned by the given method,
        using a webworker.
        """
        def method(*args, **kwargs):
            global active_future
            if active_future is not None:
                active_future.cancel()
                active_future = None

            active_future = f(*args, **kwargs)
            def callback(future):
                active_future.cancel()
                active_future = None
                try:
                    document.getElementById("vitrine").innerHTML = future.result().data.to_dict()['result']
                except CancelledError:
                    pass
                except:
                    traceback.print_exc()
                    document.getElementById("vitrine").innerHTML = '<div class="entry"><h3>Error callback</h3><pre>' + escape(traceback.format_exc()) + '</pre></div>'
            active_future.add_done_callback(callback)

        return method

    @updates_vitrine
    def single(request):
        print("Preparing vitrine worker")
        data = request.responseText
        return worker.post_message(webworker.Message('vitrine', {'data': data}), want_reply=True)

    class BothCallback:
        def __init__(self):
            self.main = None
            self.diff = None

        def onmain(self, request):
            self.main = request.responseText
            if self.main is not None and self.diff is not None:
                self.done()

        def ondiff(self, request):
            self.diff = request.responseText
            if self.main is not None and self.diff is not None:
                self.done()

        @updates_vitrine
        def done(self):
            print("Preparing hamburglar worker")
            return worker.post_message(webworker.Message('hamburglar', {'main': self.main, 'diff': self.diff}), want_reply=True)

    if left == "None" and right == "None":
        #window.location = "about"
        return
    elif left == "None":
        req = ajax.ajax()
        req.open("GET", BURGER_DATA_PREFIX + right + ".json", True)
        req.bind("complete", single)
        req.send()
    elif right == "None":
        req = ajax.ajax()
        req.open("GET", BURGER_DATA_PREFIX + left + ".json", True)
        req.bind("complete", single)
        req.send()
    else:
        callback = BothCallback()
        req = ajax.ajax()
        req.open("GET", BURGER_DATA_PREFIX + left + ".json", True)
        req.bind("complete", callback.onmain)
        req.send()
        req = ajax.ajax()
        req.open("GET", BURGER_DATA_PREFIX + right + ".json", True)
        req.bind("complete", callback.ondiff)
        req.send()

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