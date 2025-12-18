 # Concept
 
- The website should be functional even if scripting is disabled in the browser.
- The only exception to this is the audio player, which requires JavaScript to function.
- When browsing the site with javascript disabled, users will not see the audio player or any reference to it. Instead, they still can download any mod file to play it locally.
- At the same time, when scripting is enabled, the website will be "enhanced" with script features such as the audio player, dynamic loading of content, and so on.
- When scripting is enabled, the website acts as a single-page application (SPA) where possible, avoiding full page reloads. This is mainly to ensure that that the audio player is not interrupted when navigating the site.
 
 # Implementation details
- The website is built using Django templates and views, with progressive enhancement provided by JavaScript.
- UI elements that should NOT be visible when scripting is disabled are marked with the `scriptEnabled` CSS class. This class is hidden by default using CSS.  
  An example of this is the "Listen" button on song pages.
- UI elements that need script-enabled (the player) are dynamically added to the page using JavaScript once the page has loaded.
- The player is injected into a placeholder `<div>` with the id `player`. This placeholder is present in the HTML at all times, but is empty when scripting is disabled.
- The allow the site to switch to a single-page application (SPA) mode when scripting is enabled, the main content of the page is wrapped in a `<main>` element. This allows JavaScript to easily replace only the content of this element when navigating to a new page via AJAX. this assumes that all pages use the same base template, including the navbar.
  Small caveat and a "Note to Self" : is we ever encounter a page that needs additional CSS or Script files that are not part of the base template, we will need to address this separately.

# When scripting is enabled, the following happens:
1. The `scriptEnabled` CSS class is made visible using JavaScript.
2. The audio player HTML is dynamically created and injected into the `player` `<div>`.
3. Event listeners are added to the player controls to handle playback, track selection, and other interactions.
4. There is a global "click handler" installed that intercepts all clicks on the document. This is used to intercept internal navigation links. So instead of allowing the browser to perform a full page reload, an AJAX request is made to fetch the new content, which is then injected into the page. The browser history is also updated using the History API to reflect the new URL. This ONLY happens when the player is active. When no song is player, the default browser behavior of a full page reload is allowed.
5. Forms are also handled via AJAX when the player is active, to avoid page reloads. This is done by adding an "onsubmit" event listener to all forms on the page. When a form is submitted, the default behavior is prevented (when the player is active), and an AJAX request is made instead. The (HTML) response is then used to update the page content as needed.