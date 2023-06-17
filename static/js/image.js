var images = ["/static/images/ps5.jpg", "/static/images/xbox.jpg", "/static/images/switch.jpg", "/static/images/pc.jpg"];

var randomImage = images[Math.floor(Math.random() * images.length)];

var image = "<img class='img-fluid rounded' src='" + randomImage + "'>";

document.getElementById("img-random").innerHTML = image;