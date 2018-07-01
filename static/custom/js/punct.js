function clean_linefeed(puncts) {
    for (var i = 0; i < puncts.length; ++i) {
        var punct_lst = [];
        for (var j = 0; j < puncts[i].length; ++j) {
            var pos = puncts[i][j][0];
            var ch = puncts[i][j][1];
            if (ch != '\n') {
                punct_lst.push([pos, ch]);
            }
        }
        puncts[i] = punct_lst;
    }
}

var PUNCT_LIST = '：，。；、！？‘’”“\n';
Vue.component('punct-show-seg', {
    props: ['punctseg', 'sharedata'],
    //type=1是经文
    //type=2是参考标点
    template: '\
      <span v-if="punctseg.type == 1" contenteditable="true" @input.stop.prevent="inputHandler" v-html="merged_html"></span>\
      <span v-else-if="punctseg.type == 2 && sharedata.show_refpunct" v-bind:class="punctseg.cls">{{ punctseg.text }}</span>\
      <span v-else-if="punctseg.type == 3 && sharedata.show_refpunct"><br /></span>\
    ',
    data: function() {
        return {
            merged_html: ''
        }
    },
    created: function() {
        this.createMergedHtml();
    },
    methods: {
        cleanPunct: function(str) {
            var ch_lst = [];
            for (var i = 0; i < str.length; ++i) {
              if (PUNCT_LIST.indexOf(str[i]) == -1) {
                ch_lst.push(str[i]);
              }
            }
            return ch_lst.join('');
        },
        /**
         * 产生标点与文本合并之后的HTML，
         * 例如："。世間，淨眼品“？第一之一；"
         */
        createMergedHtml: function() {
            if (this.punctseg.type == 1) {
                var html_lst = [];
                var user_punct_idx = 0;
                var text_start_offset = 0;
                while (true) {
                    //这一段代码找出this.punctseg.text中需要展示的一段经文。始于text_start_offset，结束于下一个标点符号。
                    //如果经文已经全部展示，则表明数据已经全部处理完，可以退出循环了。
                    var text_end_offset = this.punctseg.text.length;
                    if (user_punct_idx < this.punctseg.user_puncts.length) {
                        text_end_offset = this.punctseg.user_puncts[user_punct_idx][0] - this.punctseg.position;
                    }
                    if (text_start_offset == text_end_offset && text_end_offset != 0 ) {
                        break;
                    }
                    var text = this.punctseg.text.substr(text_start_offset, text_end_offset - text_start_offset);
                    html_lst.push('<span class="puncttext">' + text + '</span>');

                    //下面这一段代码处理连续出现的标点符号，例如：
                    //  "。世間，淨眼品“？第一之一；"中的"“？"两个标点
                    var user_punct_lst = [];
                    while (user_punct_idx < this.punctseg.user_puncts.length
                        && text_end_offset == (this.punctseg.user_puncts[user_punct_idx][0] - this.punctseg.position)) {
                        var punct_ch = this.punctseg.user_puncts[user_punct_idx][1];
                        if (punct_ch == '\n') {
                            user_punct_lst.push('<br />');
                        } else {
                            user_punct_lst.push(punct_ch);
                        }
                        user_punct_idx++;
                    }
                    if (user_punct_lst.length > 0) {
                        html_lst.push('<span class="userpunct">' + user_punct_lst.join('') + '</span>');
                    }

                    //向前移动
                    text_start_offset = text_end_offset;
                }
                this.merged_html = html_lst.join('');
            }
        },
        getNodeIndex: function (node) {
            var n = 0;
            while (node = node.previousSibling) {
                n++;
            }
            return n;
        },
        inputHandler: function(e) {
            var selection = window.getSelection();
            var cursor_offset = selection.focusOffset;
            var focusNode = selection.focusNode;
            var parentNode = focusNode.parentNode;
            var parentNodeIndex = this.getNodeIndex(parentNode);
            // console.log('cursor_offset: ', cursor_offset);
            // console.log('focusNode: ', focusNode);
            // console.log('parent: ', parentNode, parentNodeIndex, e.target);

            var newtext = e.target.innerText;
            
            if (this.cleanPunct(newtext) == this.cleanPunct(this.punctseg.text)) {
                //更新用户标点数据
                var new_user_puncts = [];
                var text_offset = 0;
                for (var i = 0; i < newtext.length; ++i) {
                    if (PUNCT_LIST.indexOf(newtext[i]) != -1) {
                        var pos = this.punctseg.position + text_offset;
                        new_user_puncts.push([pos, newtext[i]]);
                    } else {
                        ++text_offset;
                    }
                }
                this.punctseg.user_puncts = new_user_puncts;
                this.createMergedHtml();

                // set cursor position
                this.$nextTick(function(){
                    var offset = cursor_offset;
                    parentNode = e.target.childNodes[parentNodeIndex];
                    focusNode = parentNode.firstChild;
                    while (focusNode.length < offset) {
                        offset = offset - focusNode.length;
                        parentNode = parentNode.nextSibling;
                        focusNode = parentNode.firstChild;
                    }
                    var range = document.createRange();
                    range.selectNode(focusNode);
                    range.setStart(focusNode, offset);
                    range.collapse(true);
                    e.target.focus();
                    selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);
                 });
            } else {
                //还原用户标点数据
                e.target.innerHTML = this.merged_html;
                this.$nextTick(function(){
                    parentNode = e.target.childNodes[parentNodeIndex];
                    focusNode = parentNode.firstChild;
                    var range = document.createRange();
                    range.selectNode(focusNode);
                    var offset = cursor_offset - 1;
                    if (e.isComposing) {
                        offset = cursor_offset;
                    }
                    range.setStart(focusNode, offset);
                    range.collapse(true);
                    e.target.focus();
                    selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range); 
                });
            }
        }
    }
});