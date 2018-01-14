function count_ch(s, ch) {
    var count = 0;
    for (var i = 0; i < s.length; ++i) {
        if (s[i] == ch) {
            ++count;
        }
    }
    return count;
};

function pad(num, size) {
    var s = num + "";
    while (s.length < size) s = "0" + s;
    return s;
}

function setImg(img_url, x, y, w, h) {
    var canvas = document.getElementById("page-canvas");
    var context = canvas.getContext("2d");
    var image = new Image();
    image.onload = function () {
        canvas.width = canvas.width;
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(image, 0, 0, 800, 1080);
        var xratio = 800 / image.width;
        var yratio = 1080 / image.height;
        x = parseInt(x * xratio);
        y = parseInt(y * yratio);
        w = parseInt(w * xratio);
        h = parseInt(h * yratio);
        context.moveTo(x, y);
        context.lineTo(x + w, y);
        context.lineTo(x + w, y + h);
        context.lineTo(x, y + h);
        context.lineTo(x, y);
        //设置样式
        context.lineWidth = 1;
        context.strokeStyle = "#F5270B";
        //绘制
        context.stroke();
    };
    image.src = img_url;
}

function extract_separators(text) {
    var pages = text.replace(/\r\n/g, '\n').split('\np\n');
    if (pages[0].substr(0, 2) == 'p\n') {
        pages[0] = pages[0].substr(2);
    }
    var new_separators = [];
    var pos = 0;
    var page_index = 0;
    while (page_index < pages.length) {
        var lines = pages[page_index].split('\n');
        var i = 0;
        while (i < lines.length) {
            pos += lines[i].length;
            if (i == (lines.length - 1) && page_index != (pages.length - 1)) {
                new_separators.push([pos, 'p']);
            } else {
                new_separators.push([pos, '\n']);
            }
            ++i;
        }
        ++page_index;
    }
    return new_separators;
};
