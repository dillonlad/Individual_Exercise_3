let wordslist = [];
let wordsShows = [];
let articleIds = [];

function addWords(word){
    wordslist.push(word)
    showWords();
}

function addFromInput(){
    var word = document.getElementById('wordAddText').value;
    if (word) {
        if (word.indexOf(" ") !== -1) wordslist.push(word.replace(" ", "-"))
        else wordslist.push(word)
    }
    showWords()
    document.getElementById('wordAddText').value = "";
}

function showWords(){
    for (let word of wordslist) {
        if (wordsShows.indexOf(word) === -1) {
            var node = document.createElement("LI");
            node.id = "node" + word;
            node.className = "nodeList"
            var functionName = "removeWord('" + word + "')"
            node.innerHTML = "<a href='javascript:void(0)' onclick=" + functionName + ">&times;</a>    "
            var textnode = document.createTextNode(word);
            node.appendChild(textnode);
            document.getElementById("addedWords").appendChild(node);
            wordsShows.push(word)
        }
    }
}

function removeWord(word){
    var nodeIndex = wordsShows.indexOf(word)
    var wordsIndex = wordslist.indexOf(word)
    console.log(nodeIndex, wordsIndex)
    var list = document.getElementById("addedWords")
    list.removeChild(list.childNodes[nodeIndex])
    wordsShows.splice(nodeIndex, 1)
    wordslist.splice(wordsIndex, 1)
    if (document.getElementById(word)) document.getElementById(word).checked = false;
}

function searchWords(){
    var stringWords = wordsShows.toString()
    var div = document.getElementById('preparedReading')
    return fetch("/api/prepare-reading/" + stringWords, {
        method: 'post',
        headers: {
            'content-type': 'application/json'
        }
    }).then(function (res) {
        return res.json();
    }).then(function (data) {
        div.innerHTML = data.status;
        div.style.display = "block"
        div.scrollIntoView()
        for (let i of data.type){
            articleIds.push(i)
        }
    });
}

function sendtoEmail(){
    var email = document.getElementById('emailAddress').value;
    var ArticleIds = articleIds.toString()
    var keepUpdated = false
    if (document.getElementById("keep_updated-0").checked) keepUpdated = true
    return fetch("/api/send-articles/", {
        method: 'post',
        headers: {
            'content-type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            emailAddress: email,
            articleIds: ArticleIds,
            signUp: keepUpdated
        })
    }).then(function (res){
        return res.json();
    }).then(function (data){
        alert(data.status)
    })
}