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
    while (text_idx <= text.length) {
      // 找到当前最小的punct位置
        var min_pos = text.length + 1;
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

        if (min_pos <= text.length) { // 找到了
            if (text_idx < min_pos) {
                var text_seg = text.substr(text_idx, min_pos - text_idx);
                var user_puncts = [];
                if (result_idx < result_len && punct_result[result_idx][0] <= min_pos) {
                    var strs = [];
                    var t_idx = 0;
                    while (result_idx < result_len) {
                        if (punct_result[result_idx][0] > min_pos) {
                            break;
                        }
                        if (punct_result[result_idx][0] - text_idx == t_idx) {
                            strs.push(punct_result[result_idx][1]);
                            user_puncts.push(punct_result[result_idx]);
                            ++result_idx;
                        } else if (punct_result[result_idx][0] - text_idx > t_idx) {
                            var s = text_seg.substr(t_idx, punct_result[result_idx][0] - text_idx - t_idx);
                            strs.push(s);
                            t_idx = punct_result[result_idx][0] - text_idx;
                        }
                    }
                    text_seg = strs.join('');
                }
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
            var index = indexs[min_punct_index];
            var cls = 'punct' + (min_punct_index + 1).toString();
            var punct_obj = puncts[min_punct_index][index];
            var punct_str = punct_obj[1];
            if (punct_str == '\n') {
                var punctseg = {
                    type: TYPE_BR,
                    position: text_idx,
                    text: '', // 经文或合并的标点
                    cls: '', // 显示标点的样式
                    user_puncts: []
                };
                punctseg_lst.push(punctseg);
            } else {
                var punctseg = {
                    type: TYPE_SEP,
                    position: text_idx,
                    text: punct_obj[1], // 经文或合并的标点
                    cls: cls, // 显示标点
                    user_puncts: []
                };
                punctseg_lst.push(punctseg);
            }
            indexs[min_punct_index] += 1;
        } else {
            if (text_idx < text.length) {
                var text_seg = text.substr(text_idx);
                var user_puncts = [];
                if (result_idx < result_len && punct_result[result_idx][0] <= text.length) {
                    var strs = [];
                    var t_idx = 0;
                    while (result_idx < result_len) {
                        if (punct_result[result_idx][0] > text.length) {
                            break;
                        }
                        if (punct_result[result_idx][0] - text_idx == t_idx) {
                            strs.push(punct_result[result_idx][1]);
                            user_puncts.push(punct_result[result_idx]);
                            ++result_idx;
                        } else if (punct_result[result_idx][0] - text_idx > t_idx) {
                            var s = text_seg.substr(t_idx, punct_result[result_idx][0] - text_idx - t_idx);
                            strs.push(s);
                            t_idx = punct_result[result_idx][0] - text_idx;
                        }
                    }
                    text_seg = strs.join('');
                }
                var punctseg = {
                    type: TYPE_TEXT,
                    editable: true,
                    position: text_idx,
                    text: text_seg, // 经文或合并的标点
                    cls: '', // 显示标点的颜色
                    user_puncts: user_puncts
                };
                punctseg_lst.push(punctseg);
                text_idx = text.length;
            } else {
                break;
            }
        }
    }

    console.log(punctseg_lst)
    return punctseg_lst;
}

var PUNCT_LIST = '，。：\r\n';
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
            // var punctseg = this.punctseg;
            // if (punctseg.user_puncts.length == 0) {
            //     this.merged_html = punctseg.text;
            //     return ;
            // }
            // var text = punctseg.text;
            // var text_idx = 0;
            // var html_lst = [];
            // for (var i = 0; i < punctseg.user_puncts.length; ++i) {
            //     var punct_pos = punctseg.user_puncts[i][0];
            //     var punct_offset = punct_pos - punctseg.position;
            //     var punct_ch = punctseg.user_puncts[i][1];
            //     if (text_idx < punct_offset) {
            //         html_lst.push(text.substr(text_idx, punct_offset-text_idx));
            //         text_idx = punct_offset;
            //     }
            //     html_lst.push('<span style="color:red">' + punct_ch + '</span>');
            // }
            // if (text_idx < text.length) {
            //     html_lst.push(text.substr(text_idx));
            // }
            // this.merged_html = html_lst.join('');
            //console.log('merged: ', this.merged_html);
        },
        inputHandler: function(e) {
            var selection = window.getSelection();
            var cursor_offset = selection.focusOffset;

            var newtext = e.target.innerText;
            console.log(newtext, newtext.indexOf('\r'), newtext.indexOf('\n'))
            console.log(e.target.innerHTML);
            
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
                // // set cursor position
                // window.el = e.target;
                // setTimeout(function(){
                //     console.log('set caret')
                //     var textNode = e.target.firstChild;
                //     console.log('textNode: ', textNode);
                //     var caret = cursor_offset;
                //     console.log('caret: ', caret);
                //     var range = document.createRange();
                //     range.setStart(textNode, caret);
                //     range.setEnd(textNode, caret);
                //     e.target.focus();
                //     selection = window.getSelection();
                //     selection.removeAllRanges();
                //     selection.addRange(range); 
                // }, 2000);
            } else {
                e.target.innerText = this.punctseg.text;
            }
            setTimeout(function(){
                var textNode = e.target.firstChild;
                var range = document.createRange();
                range.selectNode(textNode)
                range.setStart(textNode, cursor_offset);
                range.collapse(true);
                e.target.focus();
                selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range); 
            }, 10);
        }
    }
});