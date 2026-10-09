import os
import time
from typing import Annotated
from typing import Any

from playwright.async_api import Page

from ae.config import SOURCE_LOG_FOLDER_PATH
from ae.core.playwright_manager import PlaywrightManager
from ae.utils.dom_helper import wait_for_non_loading_dom_state
from ae.utils.get_detailed_accessibility_tree import do_get_accessibility_info
from ae.utils.logger import logger
from ae.utils.ui_messagetype import MessageType

# Edit #########################
import random
from collections import deque
import aiohttp

CLASSIFIER_THRESHOLD = 0.3
scenario = os.environ["SCENARIO"]


# ------------------------------
# DOM shuffle (unchanged)
# ------------------------------
def shuffle_siblings_bfs(root):
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if isinstance(node, dict):
            children = node.get("children")
            if isinstance(children, list):
                random.shuffle(children)
                for child in children:
                    queue.append(child)


# ------------------------------
# Classifier query (unchanged)
# ------------------------------
async def query_classifier(texts):
    url = "http://localhost:5555/classify"
    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"texts": texts}, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Classifier server error: {resp.status}")
            result = await resp.json()
            return result.get("scores")


# ------------------------------
# DOM flatten / delete (unchanged)
# ------------------------------
def flatten(data):
    flat = []
    stack = [((), data)]

    while stack:
        path, value = stack.pop()

        if isinstance(value, dict):
            for k, v in value.items():
                if k in ["children", "name", "description", "value", "aria-label"]:
                    stack.append((path + (k,), v))
        elif isinstance(value, list):
            for i, v in enumerate(value):
                stack.append((path + (i,), v))
        else:
            flat.append((path, value))

    return flat


def delete_by_path(root, path):
    cur = root
    try:
        for p in path[:-1]:
            cur = cur[p]
        last = path[-1]
        if isinstance(cur, dict):
            cur.pop(last, None)
        elif isinstance(cur, list):
            cur.pop(last)
    except Exception:
        print("❌ [CRITICAL] Failed to delete path:", path)


async def filter_elements_by_classifer(root):
    flat = flatten(root)
    contents = [val for _, val in flat]
    results = await query_classifier(contents)

    delete_paths = [
        path for (path, _), adv in zip(flat, results)
        if adv > CLASSIFIER_THRESHOLD
    ]

    for text, adv in zip(contents, results):
        tag = "❌" if adv > CLASSIFIER_THRESHOLD else "✅"
        print(f"{tag} [DOM] {adv:.4f} | {str(text)[:50].replace(chr(10),' ')}")

    for path in delete_paths:
        delete_by_path(root, path)

    return root

def split_text_chunks(text, max_len=200):
    lines = text.split("\n")
    chunks = []
    buf = ""

    for line in lines:
        if len(buf) + len(line) <= max_len:
            buf += " " + line
        else:
            chunks.append(buf.strip())
            buf = line

    if buf.strip():
        chunks.append(buf.strip())

    return chunks


async def filter_text_only_by_classifier(text: str) -> str:
    chunks = split_text_chunks(text)
    scores = await query_classifier(chunks)

    kept_chunks = []
    for chunk, score in zip(chunks, scores):
        if score <= CLASSIFIER_THRESHOLD:
            kept_chunks.append(chunk)
            print(f"✅ [TEXT] {score:.4f} | {chunk[:60]}")
        else:
            print(f"❌ [TEXT FILTERED] {score:.4f} | {chunk[:60]}")

    return "\n".join(kept_chunks)
########################

async def get_dom_with_content_type(
    content_type: Annotated[str, "The type of content to extract: 'text_only': Extracts the innerText of the highest element in the document and responds with text, or 'input_fields': Extracts the text input and button elements in the dom."]
    ) -> Annotated[dict[str, Any] | str | None, "The output based on the specified content type."]:
    """
    Retrieves and processes the DOM of the active page in a browser instance based on the specified content type.

    Parameters
    ----------
    content_type : str
        The type of content to extract. Possible values are:
        - 'text_only': Extracts the innerText of the highest element in the document and responds with text.
        - 'input_fields': Extracts the text input and button elements in the DOM and responds with a JSON object.
        - 'all_fields': Extracts all the fields in the DOM and responds with a JSON object.

    Returns
    -------
    dict[str, Any] | str | None
        The processed content based on the specified content type. This could be:
        - A JSON object for 'input_fields' with just inputs.
        - Plain text for 'text_only'.
        - A minified DOM represented as a JSON object for 'all_fields'.

    Raises
    ------
    ValueError
        If an unsupported content_type is provided.
    """

    logger.info(f"Executing Get DOM Command based on content_type: {content_type}")
    start_time = time.time()
    # Create and use the PlaywrightManager
    browser_manager = PlaywrightManager(browser_type='chromium', headless=False)
    page = await browser_manager.get_current_page()
    if page is None: # type: ignore
        raise ValueError('No active page found. OpenURL command opens a new page.')

    extracted_data = None
    await wait_for_non_loading_dom_state(page, 2000) # wait for the DOM to be ready, non loading means external resources do not need to be loaded
    user_success_message = ""
    if content_type == 'all_fields':
        user_success_message = "Fetched all the fields in the DOM"
        extracted_data = await do_get_accessibility_info(page, only_input_fields=False)
    elif content_type == 'input_fields':
        logger.debug('Fetching DOM for input_fields')
        extracted_data = await do_get_accessibility_info(page, only_input_fields=True)
        if extracted_data is None:
            return "Could not fetch input fields. Please consider trying with content_type all_fields."
        user_success_message = "Fetched only input fields in the DOM"
    elif content_type == 'text_only':
        # Extract text from the body or the highest-level element
        logger.debug('Fetching DOM for text_only')
        text_content = await get_filtered_text_content(page)
        # Edit ###########################################
        if "DEFENSE" in scenario:
            text_content = await filter_text_only_by_classifier(text_content)
        ##################################################
        with open(os.path.join(SOURCE_LOG_FOLDER_PATH, 'text_only_dom.txt'), 'w',  encoding='utf-8') as f:
            f.write(text_content)
        extracted_data = text_content
        user_success_message = "Fetched the text content of the DOM"
    else:
        raise ValueError(f"Unsupported content_type: {content_type}")

    # Edit #############################################
    if content_type != "text_only":
        if "DEFENSE" in scenario:
            shuffle_siblings_bfs(extracted_data)
            extracted_data = await filter_elements_by_classifer(extracted_data)
    ####################################################
    elapsed_time = time.time() - start_time
    logger.info(f"Get DOM Command executed in {elapsed_time} seconds")
    await browser_manager.notify_user(user_success_message, message_type=MessageType.ACTION)
    return extracted_data # type: ignore


async def get_filtered_text_content(page: Page) -> str:
    text_content = await page.evaluate("""
        () => {
            // Array of query selectors to filter out
            const selectorsToFilter = ['#agente-overlay'];

            // Store the original visibility values to revert later
            const originalStyles = [];

            // Hide the elements matching the query selectors
            selectorsToFilter.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(element => {
                    originalStyles.push({ element: element, originalStyle: element.style.visibility });
                    element.style.visibility = 'hidden';
                });
            });

            // Get the text content of the page
            let textContent = document?.body?.innerText || document?.documentElement?.innerText || "";

            // Get all the alt text from images on the page
            let altTexts = Array.from(document.querySelectorAll('img')).map(img => img.alt);
            altTexts="Other Alt Texts in the page: " + altTexts.join(' ');

            // Revert the visibility changes
            originalStyles.forEach(entry => {
                entry.element.style.visibility = entry.originalStyle;
            });
            textContent=textContent+" "+altTexts;
            return textContent;
        }
    """)
    return text_content

