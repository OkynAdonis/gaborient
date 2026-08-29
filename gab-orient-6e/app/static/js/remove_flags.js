// Remove regional-flag emojis from visible text (short, human comment)
(function(){
  function removeFlagsFromText(s){
    // Remove sequences of regional indicator symbols that form flag emojis
    return s.replace(/\uD83C[\uDDE6-\uDDFF]{2}/g, '');
  }

  function walk(node){
    let child = node.firstChild;
    while(child){
      if(child.nodeType === 3){ // text node
        const newText = removeFlagsFromText(child.nodeValue);
        if(newText !== child.nodeValue) child.nodeValue = newText;
      } else if(child.nodeType === 1 && child.nodeName !== 'SCRIPT' && child.nodeName !== 'STYLE'){
        walk(child);
      }
      child = child.nextSibling;
    }
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => walk(document.body)); else walk(document.body);
})();
