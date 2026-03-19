"use strict";
function dragNdrop(event) {
    var fileName = URL.createObjectURL(event.target.files[0]);
    var preview = document.getElementById("preview");
    var previewImg = document.createElement("img");
    previewImg.setAttribute("src", fileName);
    preview.innerHTML = "";
    preview.appendChild(previewImg);
}
function drag() {
    document.getElementById('uploadFile').parentNode.className = 'draging dragBox';
}
function drop() {
    document.getElementById('uploadFile').parentNode.className = 'dragBox';
}

"use strict";
function dragNdrop(event) {
    var files = event.target.files;
    var preview = document.getElementById("preview");
    preview.innerHTML = ""; // Clear the preview
    for (var i = 0; i < files.length; i++) {
        var fileName = URL.createObjectURL(files[i]);
        var previewImg = document.createElement("img");
        const file = files[i];
        const fileType = file['type'];
        const validImageTypes = ['image/jpeg', 'image/png'];
        if (!validImageTypes.includes(fileType)) {
            // invalid file type code goes here.
            alert("Invalid file type");
        }
        else{
            previewImg.setAttribute("src", fileName);
            preview.appendChild(previewImg);
        }
    }
}
function drag() {
    document.getElementById('uploadFile').parentNode.className = 'draging dragBox';
}
function drop() {
    document.getElementById('uploadFile').parentNode.className = 'dragBox';
}
