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

function merge_text_punct(text, puncts, punct_result) {
    clean_linefeed(puncts);
    var TYPE_TEXT = 1;
    var TYPE_SEP = 2;
    var TYPE_BR = 3;

    var result_idx = 0;
    var result_len = punct_result.length;

    var punctseg_lst = [];
    var char_lst = this.char_lst;
    var indexs = [];
    for (var i = 0; i < puncts.length; ++i) {
        indexs.push(0);
    }
    var text_idx = 0;
    while (1) {
      // 找到当前最小的punct位置
        var min_pos = text.length;
        var min_punct_index = -1;
        for (var i = 0; i < puncts.length; ++i) {
            var index = indexs[i];
            if (index < puncts[i].length) {
                var punct_obj = puncts[i][index];
                if (punct_obj[0] < min_pos) {
                    min_pos = punct_obj[0];
                    min_punct_index = i;
                }
            }
        }

        if (text_idx < min_pos) {
            var text_seg = text.substr(text_idx, min_pos - text_idx);
            var user_puncts = [];
            var strs = [];
            var t_idx = 0;
            while (result_idx < result_len && 
                (punct_result[result_idx][0] < min_pos ||
                    (punct_result[result_idx][0] == min_pos && punct_result[result_idx][1] != '\n'))) {
                if (punct_result[result_idx][0] - text_idx > t_idx) {
                    var s = text_seg.substr(t_idx, punct_result[result_idx][0] - text_idx - t_idx);
                    strs.push(s);
                    t_idx = punct_result[result_idx][0] - text_idx;
                }

                strs.push(punct_result[result_idx][1]);
                user_puncts.push(punct_result[result_idx]);
                ++result_idx;
            }
            if (t_idx < text_seg.length) {
                var s = text_seg.substr(t_idx, text_seg.length - t_idx);
                strs.push(s);
            }
            text_seg = strs.join('');
            var punctseg = {
                type: TYPE_TEXT,
                position: text_idx,
                text: text_seg, // 经文或合并的标点
                cls: '', // 显示标点的样式
                user_puncts: user_puncts
            };
            punctseg_lst.push(punctseg);
            text_idx = min_pos;
        }

        // 插入标点
        if (min_punct_index != -1) {
            var index = indexs[min_punct_index];
            var cls = 'punct' + (min_punct_index + 1).toString();
            var punct_obj = puncts[min_punct_index][index];
            var punct_str = punct_obj[1];
            var punctseg = {
                type: TYPE_SEP,
                position: text_idx,
                text: punct_obj[1], // 经文或合并的标点
                cls: cls, // 显示标点
                user_puncts: []
            };
            punctseg_lst.push(punctseg);
            indexs[min_punct_index] += 1;
        } else {
            if (text_idx == text.length) {
                break;
            }
        }
    }

    return punctseg_lst;
}

var PUNCT_LIST = '：，。；、！？\n';
Vue.component('punct-show-seg', {
    props: ['punctseg'],
    template: '\
      <span v-if="punctseg.type == 1" contenteditable="true" @input.stop.prevent="inputHandler" v-html="merged_html"></span>\
      <span v-else-if="punctseg.type == 2" v-bind:class="punctseg.cls">{{ punctseg.text }}</span>\
      <span v-else-if="punctseg.type == 3"><br /></span>\
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
        createMergedHtml: function() {
            if (this.punctseg.type == 1) {
                var html_lst = [];
                for (var i = 0; i < this.punctseg.text.length; ++i) {
                    var ch = this.punctseg.text[i];
                    if (ch == '\n') {
                        html_lst.push('<br />');
                    } else if (PUNCT_LIST.indexOf(ch) != -1) {
                        html_lst.push('<span class="userpunct">' + ch + '</span>');
                    } else {
                        html_lst.push(ch);
                    }
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
            var focusNodeIndex = this.getNodeIndex(focusNode);
            //console.log('focusNode: ', focusNode, focusNodeIndex, e.target )

            var newtext = e.target.innerText;
            
            if (this.cleanPunct(newtext) == this.cleanPunct(this.punctseg.text)) {
                var new_user_puncts = [];
                var offset = 0;
                for (var i = 0; i < newtext.length; ++i) {
                    if (PUNCT_LIST.indexOf(newtext[i]) != -1) {
                        var pos = this.punctseg.position + offset;
                        new_user_puncts.push([pos, newtext[i]]);
                    } else {
                        ++offset;
                    }
                }
                this.punctseg.user_puncts = new_user_puncts;
                this.punctseg.text = newtext;
                this.createMergedHtml();
                // set cursor position
                setTimeout(function(){
                    if (focusNodeIndex+1 < e.target.childNodes.length) {
                        var textNode = e.target.childNodes[focusNodeIndex+1];
                        var range = document.createRange();
                        range.selectNode(textNode);
                        range.setStart(textNode, 1);
                        range.collapse(true);
                        e.target.focus();
                        selection = window.getSelection();
                        selection.removeAllRanges();
                        selection.addRange(range);
                    } else {
                        var range = document.createRange();
                        range.selectNode(textNode);
                        range.setStart(textNode, 1);
                        range.collapse(true);
                        e.target.focus();
                        selection = window.getSelection();
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                }, 100);
            } else {
                e.target.innerText = this.punctseg.text;
                setTimeout(function(){
                    var focusNode = e.target.childNodes[focusNodeIndex];
                    var range = document.createRange();
                    range.selectNode(focusNode);
                    range.setStart(focusNode, cursor_offset-1);
                    range.collapse(true);
                    e.target.focus();
                    selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range); 
                }, 100);
            }
            //console.log(e, cursor_offset);
        }
    }
});