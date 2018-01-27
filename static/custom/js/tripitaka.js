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

// judge
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

Vue.component('diffseg-box', {
    props: ['diffseg', 'segindex', 'sharedata'],
    template: '\
    <div class="diffseg-box" @click.stop.prevent="click">\
        <div>{{ diffseg.base_text }}</div>\
        <span v-for="(text_diffsegtexts, index) in diffseg.text_diffsegtexts_map">\
            <span v-html="diffsegtextsJoin(text_diffsegtexts.diffsegtexts)"></span>\
            <span v-if="text_diffsegtexts.text">：{{ text_diffsegtexts.text }}</span>\
            <span v-else>为空</span>\
            <span v-if="index < (diffseg.text_diffsegtexts_map.length - 1)">；</span>\
            <span v-else>。</span>\
        </span>\
        <div>\
            <a href="#" class="diffseg-btn" @click.stop.prevent="doJudge(segindex)">判取</a>\
            <a href="#" class="diffseg-btn" @click.stop.prevent="doJudge(segindex)">存疑</a>\
            <a href="#" class="diffseg-btn" @click.stop.prevent="doMerge(segindex)">合并</a>\
            <a href="#" class="diffseg-btn" @click.stop.prevent="doSplit(segindex)">拆分</a>\
        </div>\
        <div>处理结果：{{ getResult(diffseg) }}\
        </div>\
    </div>',
    methods: {
        click: function() {
            this.sharedata.segid = this.diffseg.id;
        },
        doJudge: function(segindex) {
            this.sharedata.segindex = segindex;
            this.sharedata.judgeDialogVisible = true;
        },
        doMerge: function(segindex) {
            this.sharedata.segindex = segindex;
            this.sharedata.mergeDialogVisible = true;
        },
        doSplit: function(segindex) {
            this.sharedata.segindex = segindex;
            this.sharedata.splitDialogVisible = true;
        },
        diffsegtextsJoin: function(diffsegtexts) {
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
        },
        getResult: function(diffseg) {
            var s = '';
            if (diffseg.selected == 1) {
                if (diffseg.doubt == 0) {
                    s = '已判取，' + diffseg.selected_tname + '为正。'
                } else if (diffseg.doubt == 1) {
                    s = diffseg.selected_tname + '为正，已存疑，'
                    + diffseg.doubt_comment + '。'
                }
            }
            return s;
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
            <el-button type="primary" @click="handleOK">确定</el-button>\
            <el-button @click="handleCancel">取消</el-button>\
        </span>\
    </el-dialog>\
    ',
    data: function() {
        return {
            diffseg_id: '',
            selected_text: '',
            doubt: '',
            doubt_comment: '',
            error: null
        }
    },
    methods: {
        handleOpen: function() {
            this.diffseg_id = this.sharedata.diffseg_lst[this.sharedata.segindex].id;
            this.selected_text = this.sharedata.diffseg_lst[this.sharedata.segindex].selected_text;
            this.doubt = this.sharedata.diffseg_lst[this.sharedata.segindex].doubt;
            this.doubt_comment = this.sharedata.diffseg_lst[this.sharedata.segindex].doubt_comment;
        },
        handleOK: function() {
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
                vm.$emit('reload');
                vm.sharedata.judgeDialogVisible = false;
            })
            .catch(function(error) {
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
            return tnames.join('/');
        }
    }
})

Vue.component('merge-dialog', {
    props: ['sharedata'],
    template: '\
    <el-dialog title="合并" :visible.sync="sharedata.mergeDialogVisible" width="30%" @open="handleOpen" :before-close="handleCancel">\
        <p>选择待合并的校勘记</p>\
        <ul>\
            <li v-for="diffseg in diffsegs">\
            <input type="checkbox" :id="diffseg.id" :value="diffseg.id" v-model="diffseg_ids" />\
            <label :for="diffseg.id">{{ diffseg.base_text }}</label>\
            </li>\
        </ul>\
        <span slot="footer" class="dialog-footer">\
            <span class="alert alert-danger" v-if="error">{{ error }}</span>\
            <el-button type="primary" @click="handleOK">合并</el-button>\
            <el-button @click="handleCancel">取消</el-button>\
        </span>\
    </el-dialog>\
    ',
    data: function() {
        return {
            diffseg_id: '',
            base_pos: 0,
            diffsegs: [],
            diffseg_ids: [],
            error: null
        }
    },
    methods: {
        handleOpen: function() {
            this.diffseg_id = this.sharedata.diffseg_lst[this.sharedata.segindex].id;
            this.diffseg_ids = [this.diffseg_id];
            console.log(this.diffseg_ids);
            this.base_pos = this.sharedata.diffseg_lst[this.sharedata.segindex].base_pos;
            var vm = this;
            axios.get('/api/judge/' + this.sharedata.task_id +
            '/diffsegs/' + this.diffseg_id + '/merge_list?base_pos=' + this.base_pos)
            .then(function(response) {
                vm.diffsegs = response.data.diffsegs;
            })
        },
        handleOK: function() {
            var vm = this;
            var url = '/api/judge/' + this.sharedata.task_id + '/diffsegs/merge';
            axios.post(url, {
                diffseg_ids: vm.diffseg_ids
            })
            .then(function(response) {
                vm.$emit('reload');
                vm.sharedata.mergeDialogVisible = false;
            })
            .catch(function(error) {
                vm.error = '提交出错！';
            });
        },
        handleCancel: function() {
            this.sharedata.mergeDialogVisible = false;
            this.error = null;
        }
    }
})

Vue.component('split-dialog', {
    props: ['sharedata'],
    template: '\
    <el-dialog title="拆分" :visible.sync="sharedata.splitDialogVisible" width="50%" @open="handleOpen" :before-close="handleCancel">\
        <button class="btn" @click="incrementSplitCount">新增</button>\
        <button class="btn" @click="decrementSplitCount">减少</button>\
        <table class="table table-bordered table-condensed">\
            <thead>\
                <tr>\
                    <th></th>\
                    <th v-for="tname in tname_lst">{{ tname }}</th>\
                </tr>\
            </thead>\
            <tbody>\
            <tr v-for="(title, index) in title_lst">\
                <td>{{ title }}</td>\
                <td v-for="(tripitaka_id, tripitaka_index) in tripitaka_ids">\
                    <textarea cols="5" v-model="segtexts_lst[index][tripitaka_index]" @input="verifyData"></textarea>\
                </td>\
            </tr>\
            </tbody>\
        </table>\
        <span slot="footer" class="dialog-footer">\
            <span class="alert alert-danger" v-if="error">{{ error }}</span>\
            <el-button type="primary" @click="handleOK" :disabled="okDisabled">确定</el-button>\
            <el-button @click="handleCancel">取消</el-button>\
        </span>\
    </el-dialog>\
    ',
    data: function () {
        return {
            diffseg_id: '',
            split_count: 2,
            title_lst: [],
            tripitaka_ids: [],
            tname_lst: [],
            tripitaka_id_to_oldtext: {},
            segtexts_lst: {},
            okDisabled: false,
            error: null
        }
    },
    methods: {
        splitText: function(text, count) {
            var textseg_lst = [];
            var seg_length = Math.ceil(text.length / count);
            for (var i = 0; i < text.length;) {
                textseg_lst.push(text.substr(i, seg_length));
                i += seg_length;
            }
            var remained = count - textseg_lst.length;
            for (var i = 0; i < remained; ++i) {
                textseg_lst.push('');
            }
            return textseg_lst;
        },
        generateSplitItems: function() {
            this.title_lst = [];
            this.tripitaka_ids = [];
            this.tname_lst = [];
            this.tripitaka_id_to_oldtext = {};
            this.segtexts_lst = [];
            for (var i = 1; i <= this.split_count; ++i) {
                this.title_lst.push(i.toString());
                this.segtexts_lst.push([]);
            }
            var length = this.sharedata.diffseg_lst[this.sharedata.segindex].text_diffsegtexts_map.length;
            for (var i = 0; i < length; ++i) {
                var text_diffsegtexts = this.sharedata.diffseg_lst[this.sharedata.segindex].text_diffsegtexts_map[i];
                var text_lst = this.splitText(text_diffsegtexts.text, this.split_count);
                for (var j = 0; j < text_diffsegtexts.diffsegtexts.length; ++j) {
                    var tripitaka_id = text_diffsegtexts.diffsegtexts[j].tripitaka_id;
                    var tname = text_diffsegtexts.diffsegtexts[j].tname;
                    this.tripitaka_ids.push(tripitaka_id);
                    this.tname_lst.push(tname);
                    this.tripitaka_id_to_oldtext[tripitaka_id] = text_diffsegtexts.text;
                    for (var k = 0; k < this.split_count; ++k) {
                        this.segtexts_lst[k].push( text_lst[k] );
                    }
                }
            }
        },
        verifyData: function() {
            var i = 0;
            var j = 0;
            for (var i = 0; i < this.tripitaka_ids.length; ++i) {
                var tripitaka_id = this.tripitaka_ids[i];
                var texts = [];
                for (var j = 0; j < this.split_count; ++j) {
                    texts.push(this.segtexts_lst[j][i]);
                }
                var mergetext = texts.join('');
                if (mergetext != this.tripitaka_id_to_oldtext[tripitaka_id]) {
                    this.okDisabled = true;
                    return true;
                }
            }
            this.okDisabled = false;
            return false;
        },
        incrementSplitCount: function () {
            if (this.split_count < 20) {
                this.split_count++;
                this.generateSplitItems();
            }
        },
        decrementSplitCount: function () {
            if (this.split_count > 1) {
                this.split_count--;
                this.generateSplitItems();
            }
        },
        handleOpen: function () {
            this.diffseg_id = this.sharedata.diffseg_lst[this.sharedata.segindex].id;
            this.split_count = 2;
            this.generateSplitItems();
        },
        handleOK: function () {
            var vm = this;
            var url = '/api/judge/' + this.sharedata.task_id + '/diffsegs/' + this.diffseg_id + '/split';
            axios.post(url, {
                split_count: vm.split_count,
                tripitaka_ids: vm.tripitaka_ids,
                segtexts_lst: vm.segtexts_lst
            })
            .then(function(response) {
                vm.$emit('reload');
                vm.sharedata.splitDialogVisible = false;
            })
            .catch(function (error) {
                vm.error = '提交出错！';
            });
        },
        handleCancel: function() {
            this.sharedata.splitDialogVisible = false;
            this.error = null;
        }
    }
})