Vue.component('rectitem', {
    template: '<div class="flow char-image correct-char flip-inx">' +
                    '<img class="lazy" :src="clip"/>' +
                    '<span class="badge char-info" style="width: 80px;">[[item.ch]] [[item.cc]]</span>' +
                    '</div>',
    props:['item'],
    delimiters: ['[[', ']]'],
    mounted: function () {
        console.log("mounted="+this.item);
        this.loadImage(this.item);
    },
    data: function () {
        return {
            image: null,
            clip: '/static/img/FhHRx.gif',
        }
    },
    watch: {
       item: function (newRect) {
           console.log("watch="+newRect);
           this.clip = '/static/img/FhHRx.gif';
           this.loadImage(newRect);
       }
    },
    methods: {
        loadImage: function (rect) {
            if(rect){
                let columnSet = rect.column_set;
                if(!this.image){
                    this.image = new Image();
                    this.image.crossOrigin = "*";
                    this.image.onload = function(evt){
                        this.clip = this.getImageClip(evt.target, rect.w, rect.h, rect.x - columnSet.x, rect.y - columnSet.y, 1);
                    }.bind(this);
                }
                this.image.src = this.getImageUrl(columnSet.col_id);
            }
        },
        getImageUrl: function (column_code) {
            const regex = /^.*_.*/;
            if(regex.test(column_code)){
                Array.prototype.subarray=function(start,end){
                    if(!end){ end=-1;}
                   return this.slice(start, this.length+1-(end*-1));
                }
                let column_path = column_code.split('_').subarray(0,-2).join("/")
                return "https://s3.cn-north-1.amazonaws.com.cn/lqdzj-col/" + column_path + "/" + column_code + ".jpg"
            }
            //说明column_code不匹配规则, 默认显示加载中...todo 后续改加载失败的图片.
            this.clip = '/static/img/FhHRx.gif';
        },
        getImageClip: function(imgObj, newWidth, newHeight, startX, startY, ratio) {

            /* the parameters: - the image element - the new width - the new height - the x point we start taking pixels - the y point we start taking pixels - the ratio */
            //set up canvas for thumbnail

            var tnCanvas = document.createElement('canvas');
            var tnCanvasContext = tnCanvas.getContext('2d');
            var bufferCanvas = document.createElement('canvas');
            var bufferContext = bufferCanvas.getContext('2d');
            tnCanvas.width = newWidth; tnCanvas.height = newHeight;

            /* use the sourceCanvas to duplicate the entire image. This step was crucial for iOS4 and under devices. Follow the link at the end of this post to see what happens when you don’t do this */

            bufferCanvas.width = imgObj.width;
            bufferCanvas.height = imgObj.height;
            bufferContext.drawImage(imgObj, 0, 0);

            /* now we use the drawImage method to take the pixels from our bufferCanvas and draw them into our thumbnail canvas */
            tnCanvasContext.drawImage(bufferCanvas, startX, startY, newWidth * ratio, newHeight * ratio,0,0, newWidth, newHeight);
            return tnCanvas.toDataURL("image/png");
        }
    }
});