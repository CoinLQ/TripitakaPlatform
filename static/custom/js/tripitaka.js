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

function judge_merge_text_punct1(text, diffseg_pos_lst, punct_lst) {
    var lines = [];
    var line = [];
    var i = 0;
    var diffseg_idx = 0;
    var punct_idx = 0;
    var diffseg_endpos = text.length + 1;
    while (i < text.length) {
        var pos = diffseg_endpos;
        if (diffseg_idx < diffseg_pos_lst.length) {
            if (pos > diffseg_pos_lst[diffseg_idx].base_pos) {
                pos = diffseg_pos_lst[diffseg_idx].base_pos;
            }
        }
        if (punct_idx < punct_lst.length) {
            if (pos > punct_lst[punct_idx][0]) {
                pos = punct_lst[punct_idx][0];
            }
        }
        if (pos <= text.length && pos > i) {
            line.push(text.substr(i, pos-i));
            i = pos;
        } else if (pos > text.length) {
            line.push(text.substr(i));
            i = text.length;
        }

        if (i == diffseg_endpos) {
            line.push('</a>');
            diffseg_endpos = text.length + 1;
        }

        // 处理标点
        while (punct_idx < punct_lst.length) {
            if (punct_lst[punct_idx][0] == i) {
                var punct_ch = punct_lst[punct_idx][1];
                if (punct_ch == '\n') {
                    lines.push(line.join(''));
                    //console.log('line: ', line.join(''));
                    line = [];
                } else {
                    line.push(punct_ch);
                }
                ++punct_idx;
            } else {
                break;
            }
        }

        if (diffseg_idx < diffseg_pos_lst.length) {
            var pos = diffseg_pos_lst[diffseg_idx].base_pos;
            if (pos == i) {
                diffseg_endpos = pos + diffseg_pos_lst[diffseg_idx].base_length;
                if (pos == diffseg_endpos) {
                    line.push('<a href="#" class="diffseg-tag diffseg-tag-notext" id="diffseg-tag-'
                     + diffseg_pos_lst[diffseg_idx].diffseg_id + '" v-on:click="click">');
                    line.push('<span class="diffseg-tag-white"></span>');
                } else {
                    line.push('<a href="#" class="diffseg-tag" id="diffseg-tag-' + diffseg_pos_lst[diffseg_idx].diffseg_id + '">');
                }
                //console.log(line);
                
                if (diffseg_endpos == i) {
                    line.push('</a>');
                    diffseg_endpos = text.length + 1;
                }
                ++diffseg_idx;
            }

        }
    }
    return lines;
}

function judge_merge_text_punct(text, diffseg_pos_lst, punct_lst) {
    var TEXT = 0;
    var LINE_FEED = 1;
    var SEG_NOTEXT = 2;
    var SEG_TEXT = 3;
    var SEG_LINES = 4;

    var result = [];
    var i = 0;
    var diffseg_idx = 0;
    var punct_idx = 0;
    var diffseg_endpos = text.length + 1;
    var obj = null;
    while (i < text.length) {
        var pos = diffseg_endpos;
        if (diffseg_idx < diffseg_pos_lst.length) {
            if (pos > diffseg_pos_lst[diffseg_idx].base_pos) {
                pos = diffseg_pos_lst[diffseg_idx].base_pos;
            }
        }
        if (punct_idx < punct_lst.length) {
            if (pos > punct_lst[punct_idx][0]) {
                pos = punct_lst[punct_idx][0];
            }
        }
        if (pos <= text.length && pos > i) {
            if (obj != null) {
                obj['text'].push(text.substr(i, pos-i));
            } else {
                obj = {
                    'type': TEXT, // text
                    'text': [ text.substr(i, pos-i) ]
                };
            }
            i = pos;
        } else if (pos > text.length) {
            if (obj != null) {
                obj['text'].push(text.substr(i));
            } else {
                obj = {
                    'type': TEXT, // text
                    'text': [ text.substr(i) ]
                };
            }
            obj['text'] = obj['text'].join('');
            result.push(obj);
            obj = null;
            i = text.length;
        }

        if (i == diffseg_endpos) {
            if (obj != null) {
                obj['text'] = obj['text'].join('');
                if ('lines' in obj) {
                    obj['lines'].push(obj['text']);
                    obj['text'] = [];
                }
                result.push(obj);
            }
            obj = null;
            diffseg_endpos = text.length + 1;
        }

        // 处理标点
        while (punct_idx < punct_lst.length) {
            if (punct_lst[punct_idx][0] == i) {
                var punct_ch = punct_lst[punct_idx][1];
                if (punct_ch == '\n') {
                    if (obj != null) {
                        if (obj['type'] == TEXT) {
                            obj['text'] = obj['text'].join('');
                            result.push(obj);
                            obj = null;
                            result.push({
                                'type': LINE_FEED //'\n'
                            });
                        } else if (obj['type'] == SEG_TEXT) {
                            obj['type'] = SEG_LINES;
                            obj['lines'] = [obj['text'].join('')]
                            obj['text'] = [];
                        } else if (obj['type'] == SEG_LINES) {
                            obj['lines'].push(obj['text'].join(''));
                            obj['text'] = [];
                        }
                    } else {
                        result.push({
                            'type': LINE_FEED
                        });
                    }
                } else {
                    if (obj != null) {
                        obj['text'].push(punct_ch);
                    } else {
                        obj = {
                            'type': TEXT,
                            'text': [ punct_ch ]
                        }
                    }
                }
                ++punct_idx;
            } else {
                break;
            }
        }

        if (diffseg_idx < diffseg_pos_lst.length) {
            var pos = diffseg_pos_lst[diffseg_idx].base_pos;
            if (pos == i) {
                diffseg_endpos = pos + diffseg_pos_lst[diffseg_idx].base_length;
                if (obj != null) {
                    if (obj['type'] == TEXT || obj['type'] == SEG_TEXT) {
                        obj['text'] = obj['text'].join('');
                    } else if (obj['type'] == SEG_LINES) {
                        obj['lines'].push(obj['text'].join(''));
                        obj['text'] = [];
                    }
                    result.push(obj);
                    obj = null;
                }
                if (pos == diffseg_endpos) {
                    obj = {
                        'diffseg_id': diffseg_pos_lst[diffseg_idx].diffseg_id,
                        'type': SEG_NOTEXT
                    };
                    result.push(obj);
                    obj = null;
                    diffseg_endpos = text.length + 1;
                } else {
                    obj = {
                        'diffseg_id': diffseg_pos_lst[diffseg_idx].diffseg_id,
                        'type': SEG_TEXT,
                        'text': []
                    };
                }
                ++diffseg_idx;
            }

        }
    }
    return result;
}

function diffsegtexts_join(diffsegtexts) {
    var i = 0;
    var lst = [];
    while (i < diffsegtexts.length) {
        var s = '';
        if (diffsegtexts[i].pid != '') {
            s = '<a href="/sutra_pages/' + diffsegtexts[i].pid + '/view?cid=' + diffsegtexts[i].start_cid + '" target="_blank">' + diffsegtexts[i].tname + '</a>';
        } else {
            s = diffsegtexts[i].tname;
        }
        lst.push(s);
        ++i;
    }
    return lst.join('/');
}

// judge
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";
Vue.component('diffseg-box', {
    props: ['diffseg', 'segindex', 'sharedata'],
    template: '\
    <div class="diffseg-box" @click.stop.prevent="click">\
        <div>{{ diffseg.base_text }}</div>\
        <span v-for="(text_diffsegtexts, index) in diffseg.text_diffsegtexts_map">\
            <span v-html="diffsegtexts_join(text_diffsegtexts.diffsegtexts)"></span>\
            <span v-if="text_diffsegtexts.text">：{{ text_diffsegtexts.text }}</span>\
            <span v-else>为空</span>\
            <span v-if="index < (diffseg.text_diffsegtexts_map.length - 1)">；</span>\
            <span v-else>。</span>\
        </span>\
        <div><a href="#" class="diffseg-btn" @click.stop.prevent="doJudge(segindex)">判取</a><a href="#" class="diffseg-btn">存疑</a><a href="#" class="diffseg-btn">合并</a><a href="#" class="diffseg-btn">拆分</a></div>\
        <div>处理结果：<span v-if="diffseg.selected == 1 && diffseg.doubt == 0">已判取，{{ diffseg.selected_tname }}为正。</span>\
        <span v-else-if="diffseg.selected == 1 && diffseg.doubt == 1">{{ diffseg.selected_tname }}为正，已存疑，{{ diffseg.doubt_comment }}。</span>\
        </div>\
    </div>',
    created: function() {
        
    },
    methods: {
        click: function() {
            this.sharedata.segid = this.diffseg.id;
        },
        doJudge: function(segindex) {
            this.sharedata.segindex = segindex;
            this.sharedata.judgeDialogVisible = true;
        }
    }
})

// 经文显示单元
Vue.component('sutra-unit', {
    props: ['data', 'sharedata'],
    template: '\
    <span>\
        <span v-if="data.type == 0">{{ data.text }}</span>\
        <span v-else-if="data.type == 1" tag="br"><br /></span>\
        <span v-else-if="data.type == 2"><a href="#" :diffsegid="data.diffseg_id" :class="className"><span class="diffseg-tag-white"></span></a></span>\
        <span v-else-if="data.type == 3"><a href="#" :diffsegid="data.diffseg_id" :class="className">{{ data.text }}</a></span>\
        <span v-else>\
            <a href="#" :diffsegid="data.diffseg_id" :class="className">\
                <span v-for="(line, index) in data.lines" tag="seg">{{ line }}<br v-if="index < data.lines.length-1" /></span>\
            </a>\
        </span>\
    </span>\
    ',
    computed: {
        className: function() {
            if (this.data.type == 2) {
                if (this.sharedata.segid == this.data.diffseg_id) {
                    return 'diffseg-tag-notext-selected';
                } else {
                    return 'diffseg-tag-notext';
                }
            } else if (this.data.type == 3) {
                if (this.sharedata.segid == this.data.diffseg_id) {
                    return 'diffseg-tag-selected';
                }
            }
            return '';
        }
    }
})

Vue.component('judge-dialog', {
    props: ['sharedata'],
    template: '\
    <el-dialog title="判取" :visible.sync="sharedata.judgeDialogVisible" width="30%" @open="handleOpen" :before-close="handleCancel">\
        <table class="table table-bordered">\
            <thead>\
            <tr><th>判取</th><th>版本</th><th>用字</th></tr>\
            </thead>\
            <tbody>\
            <tr v-for="item in sharedata.diffseg_lst[sharedata.segindex].text_diffsegtexts_map">\
                <td>\
                    <input type="radio" v-bind:value="item.text" v-model="selected_text" />\
                </td>\
                <td>{{ joinTnames(item.diffsegtexts) }}</td>\
                <td>{{ item.text }}</td>\
            </tr>\
            </tbody>\
        </table>\
        <span>是否存疑：</span>\
        <div class="radio"><label>\
            <input type="radio" v-model="doubt" value="0" />否\
        </label></div>\
        <div class="radio"><label>\
            <input type="radio" v-model="doubt" value="1" />是\
        </label></div>\
        <div>存疑说明：</div>\
        <textarea class="form-control" rows="3" v-model="doubt_comment"></textarea>\
        <span slot="footer" class="dialog-footer">\
            <span class="alert alert-danger" v-if="error">{{ error }}</span>\
            <el-button @click="handleCancel">取 消</el-button>\
            <el-button type="primary" @click="handleOK">确 定</el-button>\
        </span>\
    </el-dialog>\
    ',
    data: function () {
        return {
            diffseg_id: this.sharedata.diffseg_lst[this.sharedata.segindex].id,
            selected_text: this.sharedata.diffseg_lst[this.sharedata.segindex].selected_text,
            doubt: this.sharedata.diffseg_lst[this.sharedata.segindex].doubt,
            doubt_comment: this.sharedata.diffseg_lst[this.sharedata.segindex].doubt_comment,
            error: null
        }
    },
    methods: {
        handleOpen: function () {
            this.diffseg_id = this.sharedata.diffseg_lst[this.sharedata.segindex].id;
            this.selected_text = this.sharedata.diffseg_lst[this.sharedata.segindex].selected_text;
            this.doubt = this.sharedata.diffseg_lst[this.sharedata.segindex].doubt;
            this.doubt_comment = this.sharedata.diffseg_lst[this.sharedata.segindex].doubt_comment;
        },
        handleOK: function () {
            console.log(this.doubt_comment)
            var vm = this;
            var url = '/api/judge/' + this.sharedata.task_id + '/diffsegs/' + this.diffseg_id + '/select';
            axios.post(url, {
                selected_text: vm.selected_text,
                doubt: vm.doubt,
                doubt_comment: vm.doubt_comment
            })
            .then(function(response) {
                vm.sharedata.diffseg_lst[vm.sharedata.segindex].selected_text = vm.selected_text;
                vm.sharedata.diffseg_lst[vm.sharedata.segindex].doubt = vm.doubt;
                vm.sharedata.diffseg_lst[vm.sharedata.segindex].doubt_comment = vm.doubt_comment;
                vm.sharedata.judgeDialogVisible = false;
            })
            .catch(function (error) {
                vm.error = '提交出错！';
            });
        },
        handleCancel: function() {
            this.sharedata.judgeDialogVisible = false;
            this.error = null;
        },
        joinTnames: function(diffsegtexts) {
            var tnames = [];
            diffsegtexts.forEach(function(e) {
                tnames.push(e.tname);                
            });
            return tnames.join('/')
        }
    }
})