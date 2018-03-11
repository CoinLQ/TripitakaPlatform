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
            } if (lines[i] == 'b') {
                new_separators.push([pos, 'b']);
            } else {
                new_separators.push([pos, '\n']);
            }
            ++i;
        }
        ++page_index;
    }
    return new_separators;
};

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
    props: ['diffsegresult', 'segindex', 'sharedata'],
    template: '\
    <div class="diffseg-box" @click.stop.prevent="click">\
        <div><span>{{ base_text }}</span>\
        <span><a href="#" @click.stop.prevent="showImage(diffsegresult)">查看列图</a></span>\
        </div>\
        <span v-for="(diffsegtexts, text, index) in diffsegresult.text_to_diffsegtexts">\
            <span v-for="(diffsegtext, idx) in diffsegtexts">\
                <span v-if="idx != 0">/</span><a href="#" @click="openPageDialog(diffsegtext)">{{ diffsegtext.tripitaka.shortname }}</a>\
            </span>\
            <span v-if="text">：{{ text }}</span>\
            <span v-else>：为空</span>\
            <span v-if="index < (diffsegresult.text_count - 1)">；</span>\
            <span v-else>。</span>\
        </span>\
        <div v-if="sharedata.is_verify" v-for="(judge_result, index) in diffsegresult.judge_results">\
            <div>\
                <span>判取{{ index + 1 }}：{{ getResult(judge_result) }}</span>\
                <a href="#" v-if="judge_result.typ == 2" @click.stop.prevent="showSplit(judge_result)">显示拆分方案</a>\
            </div>\
        </div>\
        <div>\
            <a href="#" class="diffseg-btn" @click.stop.prevent="doJudge(segindex)" :disabled="diffsegresult.typ == 2">判取</a>\
            <a href="#" class="diffseg-btn" @click.stop.prevent="doMerge(segindex)">合并</a>\
            <a href="#" class="diffseg-btn" v-if="diffsegresult.merged_diffsegresults.length == 0" @click.stop.prevent="doSplit(segindex)">拆分</a>\
        </div>\
        <div>处理结果：{{ getResult(diffsegresult) }}\
        </div>\
    </div>',
    computed: {
        base_text: function() {
            var base_tripitaka_id = this.sharedata.base_tripitaka_id;
            var length = this.diffsegresult.diffseg.diffsegtexts.length;
            var text = '';
            for (var i = 0; i < length; ++i) {
                var diffsegtext = this.diffsegresult.diffseg.diffsegtexts[i];
                if (diffsegtext.tripitaka.id == base_tripitaka_id) {
                    text = diffsegtext.text;
                    break;
                }
            }
            if (text == '') {
                text = '底本为空';
            }
            return text;
        }
    },
    methods: {
        click: function() {
            this.sharedata.diffseg_id = this.diffsegresult.diffseg.id;
            this.$emit('segfocus');
            console.log('emit segfocus')
        },
        openPageDialog: function(diffsegtext) {
            if (diffsegtext.page_url != null) {
                this.sharedata.pageDialogInfo = {
                    page_url: diffsegtext.page_url,
                    start_char_pos: diffsegtext.start_char_pos,
                    end_char_pos: diffsegtext.end_char_pos
                }
                this.sharedata.judgePageDialogVisible = true;
            }
        },
        doJudge: function(segindex) {
            if (this.diffsegresult.typ == 2) {
                return ;
            }
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
        getResult: function(diffsegresult) {
            var s = '';
            if (diffsegresult.selected == 0) {
                s += '未判取。';
            } else if (diffsegresult.doubt == 0) {
                s += diffsegresult.selected_text + '。';
            } else if (diffsegresult.doubt == 1) {
                s += diffsegresult.selected_text + '。存疑理由：' + diffsegresult.doubt_comment + '。';
            }
            var merged_length = diffsegresult.merged_diffsegresults.length;
            if (diffsegresult.typ == 1) {
                var little_count = 0;
                var great_count = 0;
                for (var i = 0; i < merged_length; ++i) {
                    var id = diffsegresult.merged_diffsegresults[i];
                    if (id < diffsegresult.id) {
                        little_count++;
                    } else if (id > diffsegresult.id) {
                        great_count++;
                    }
                }
                if (little_count != 0 || great_count != 0) {
                    var texts = [];
                    if (little_count != 0) {
                        texts.push('前' + little_count + '条');
                    }
                    if (great_count != 0) {
                        texts.push('后' + great_count + '条');
                    }
                    s += '合并结果：已与' + texts.join('、') + '合并。';
                }
            } else if (diffsegresult.typ == 2) {
                s += '拆分结果：已拆分。'
            }
            return s;
        },
        showSplit: function(judge_result) {
            this.sharedata.show_split_diffsegresult = judge_result;
            this.sharedata.showSplitDialogVisible = true;
        },
        showImage: function(diffsegresult) {
            this.sharedata.image_diffseg_id = diffsegresult.diffseg.id;
            this.sharedata.judgeImageDialogVisible = true;
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
        <span v-else-if="data.type == 2"><a href="#" :diffsegno="data.diffseg_id" :class="className" @click="showImage()"><span class="diffseg-tag-white"></span></a></span>\
        <span v-else-if="data.type == 3"><a href="#" :diffsegno="data.diffseg_id" :class="className" @click="showImage()">{{ data.text }}</a></span>\
        <span v-else>\
            <a href="#" :diffsegno="data.diffseg_id" :class="className" @click="showImage()">\
                <span v-for="(line, index) in data.lines" tag="seg">{{ line }}<br v-if="index < data.lines.length-1" /></span>\
            </a>\
        </span>\
    </span>\
    ',
    computed: {
        className: function() {
            if (this.data.type == 2) {
                if (this.sharedata.diffseg_id == this.data.diffseg_id) {
                    return 'diffseg-tag-notext-selected';
                } else {
                    return 'diffseg-tag-notext';
                }
            } else if (this.data.type == 3) {
                if (this.sharedata.diffseg_id == this.data.diffseg_id) {
                    return 'diffseg-tag-selected';
                }
            }
            return '';
        }
    },
    methods: {
        showImage: function() {
            this.sharedata.image_diffseg_id = this.data.diffseg_id;
            console.log(this.sharedata.image_diffseg_id);
            this.sharedata.judgeImageDialogVisible = true;
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
            <tbody v-if="sharedata.segindex >= 0">\
            <tr v-for="(diffsegtexts, text) in sharedata.diffsegresults[sharedata.segindex].text_to_diffsegtexts">\
                <td>\
                    <input type="radio" v-bind:value="text" v-model="selected_text" />\
                </td>\
                <td>{{ joinTnames(diffsegtexts) }}</td>\
                <td>{{ text }}</td>\
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
        <div v-show="doubt == 1">\
            <div>存疑说明：</div>\
            <textarea class="form-control" rows="3" v-model="doubt_comment"></textarea>\
        </div>\
        <span slot="footer" class="dialog-footer">\
            <span class="alert alert-danger" v-if="error">{{ error }}</span>\
            <el-button type="primary" @click="handleOK">确定</el-button>\
            <el-button @click="handleCancel">取消</el-button>\
        </span>\
    </el-dialog>\
    ',
    data: function() {
        return {
            diffsegresult_id: '',
            selected_text: '',
            doubt: '',
            doubt_comment: '',
            error: null
        }
    },
    methods: {
        handleOpen: function() {
            this.diffsegresult_id = this.sharedata.diffsegresults[this.sharedata.segindex].id;
            this.selected_text = this.sharedata.diffsegresults[this.sharedata.segindex].selected_text;
            this.doubt = this.sharedata.diffsegresults[this.sharedata.segindex].doubt;
            this.doubt_comment = this.sharedata.diffsegresults[this.sharedata.segindex].doubt_comment;
        },
        handleOK: function() {
            var vm = this;
            var url = '/api/judge/' + this.sharedata.task_id + '/diffsegresults/' + this.diffsegresult_id + '/';
            axios.put(url, {
                typ: 1,
                selected_text: vm.selected_text,
                selected: 1, 
                doubt: vm.doubt,
                doubt_comment: vm.doubt_comment,
                split_info: '{}'
            })
            .then(function(response) {
                vm.sharedata.diffsegresults[vm.sharedata.segindex].selected_text = vm.selected_text;
                vm.sharedata.diffsegresults[vm.sharedata.segindex].selected = vm.selected;
                vm.sharedata.diffsegresults[vm.sharedata.segindex].doubt = vm.doubt;
                vm.sharedata.diffsegresults[vm.sharedata.segindex].doubt_comment = vm.doubt_comment;
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
            diffsegtexts.forEach(function(diffsegtext) {
                tnames.push(diffsegtext.tripitaka.shortname);
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
            <li v-for="diffsegresult in diffsegresults">\
            <input type="checkbox" :id="diffsegresult.id" :value="diffsegresult.id" v-model="diffsegresult_ids" />\
            <label :for="diffsegresult.id">{{ getBaseText(diffsegresult) }}</label>\
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
            diffsegresult_id: '',
            base_pos: 0,
            diffsegresults: [],
            diffsegresult_ids: [],
            error: null
        }
    },
    methods: {
        getBaseText: function(diffsegresult) {
            var diffsegtexts = diffsegresult.diffseg.diffsegtexts;
            var length = diffsegtexts.length;
            var text = '';
            for (var i = 0; i < length; ++i) {
                if (diffsegtexts[i].tripitaka.id == this.sharedata.base_tripitaka_id) {
                    text = diffsegtexts[i].text;
                    break;
                }
            }
            if (text == '') {
                text = '底本为空';
            }
            return text;
        },
        handleOpen: function() {
            var diffsegresult = this.sharedata.diffsegresults[this.sharedata.segindex];
            this.diffsegresult_id = diffsegresult.id;
            this.diffsegresult_ids = [this.diffsegresult_id];
            for (var i = 0; i < diffsegresult.merged_diffsegresults.length; ++i) {
                this.diffsegresult_ids.push(diffsegresult.merged_diffsegresults[i]);
            }
            var vm = this;
            axios.get('/api/judge/' + this.sharedata.task_id +
            '/diffsegresults/' + this.diffsegresult_id + '/mergelist/')
            .then(function(response) {
                console.log(response.data)
                vm.diffsegresults = response.data;
            })
        },
        handleOK: function() {
            var vm = this;
            var merged_diffsegresults = [];
            for (var i = 0; i < this.diffsegresult_ids.length; ++i) {
                var id = this.diffsegresult_ids[i];
                if (id != this.diffsegresult_id) {
                    merged_diffsegresults.push(id);
                }
            }
            var url = '/api/judge/' + this.sharedata.task_id + 
            '/diffsegresults/' + this.diffsegresult_id + '/';
            axios.put(url, {
                typ: 1,
                merged_diffsegresults: merged_diffsegresults,
                split_info: '{}'
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
        <button class="btn" @click="decrementSplitCount">减少</button><span>减少到1将取消原先的拆分。</span>\
        <table class="table table-bordered table-condensed">\
            <thead>\
                <tr>\
                    <th></th>\
                    <th v-for="tname in tname_lst">{{ tname }}</th>\
                    <th>我的选择</th>\
                </tr>\
            </thead>\
            <tbody>\
            <tr v-for="(title, index) in title_lst">\
                <td>{{ title }}</td>\
                <td v-for="(tripitaka_id, tripitaka_index) in tripitaka_ids">\
                    <textarea cols="4" v-model="tripitaka_id_to_texts[tripitaka_id][index]" @input="verifyData"></textarea>\
                </td>\
                <td>\
                    <textarea cols="4" v-model="selected_lst[index]" @input="verifyData"></textarea>\
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
            diffsegresult_id: '',
            split_count: 2,
            title_lst: [],
            tripitaka_ids: [],
            tname_lst: [],
            tripitaka_id_to_oldtext: {},
            tripitaka_id_to_texts: {},
            selected_lst: [],
            okDisabled: true,
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
            var diffsegresult = this.sharedata.diffsegresults[this.sharedata.segindex];
            if (diffsegresult.typ == 2) {
                var split_info = JSON.parse(diffsegresult.split_info);
                this.split_count = split_info.split_count;
                this.tripitaka_id_to_texts = split_info.tripitaka_id_to_texts;
                this.selected_lst = split_info.selected_lst;
                this.title_lst = [];
                this.tripitaka_ids = [];
                this.tname_lst = [];
                this.tripitaka_id_to_oldtext = {};
                for (var i = 1; i <= this.split_count; ++i) {
                    this.title_lst.push(i.toString());
                }
                var diffsegtexts = this.sharedata.diffsegresults[this.sharedata.segindex].diffseg.diffsegtexts;
                var length = diffsegtexts.length;
                for (var i = 0; i < length; ++i) {
                    var text_lst = this.splitText(diffsegtexts[i].text, this.split_count);
                    var tripitaka_id = diffsegtexts[i].tripitaka.id;
                    var tname = diffsegtexts[i].tripitaka.shortname;
                    this.tripitaka_ids.push(tripitaka_id);
                    this.tname_lst.push(tname);
                    this.tripitaka_id_to_oldtext[tripitaka_id] = diffsegtexts[i].text;
                }
            } else {
                this.split_count = 2;
                this.title_lst = [];
                this.tripitaka_ids = [];
                this.tname_lst = [];
                this.tripitaka_id_to_oldtext = {};
                this.tripitaka_id_to_texts = {};
                this.selected_lst = [];
                for (var i = 1; i <= this.split_count; ++i) {
                    this.title_lst.push(i.toString());
                    this.selected_lst.push('');
                }
                var diffsegtexts = this.sharedata.diffsegresults[this.sharedata.segindex].diffseg.diffsegtexts;
                var length = diffsegtexts.length;
                for (var i = 0; i < length; ++i) {
                    var text_lst = this.splitText(diffsegtexts[i].text, this.split_count);
                    var tripitaka_id = diffsegtexts[i].tripitaka.id;
                    var tname = diffsegtexts[i].tripitaka.shortname;
                    this.tripitaka_ids.push(tripitaka_id);
                    this.tname_lst.push(tname);
                    this.tripitaka_id_to_oldtext[tripitaka_id] = diffsegtexts[i].text;
                    this.tripitaka_id_to_texts[tripitaka_id] = text_lst;              
                }
            }
        },
        verifyData: function() {
            var i = 0;
            var j = 0;
            for (var i = 0; i < this.tripitaka_ids.length; ++i) {
                var tripitaka_id = this.tripitaka_ids[i];
                var mergetext = this.tripitaka_id_to_texts[tripitaka_id].join('');
                if (mergetext != this.tripitaka_id_to_oldtext[tripitaka_id]) {
                    this.okDisabled = true;
                    return true;
                }
            }
            for (var i = 0; i < this.split_count; ++i) {
                if (this.selected_lst[i] == undefined) {
                    this.selected_lst[i] = '';
                }
                var match = false;
                for (var j = 0; j < this.tripitaka_ids.length; ++j) {
                    var tripitaka_id = this.tripitaka_ids[j];
                    if (this.tripitaka_id_to_texts[tripitaka_id][i] == this.selected_lst[i]) {
                        match = true;
                    }
                }
                if (!match) {
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
            this.diffsegresult_id = this.sharedata.diffsegresults[this.sharedata.segindex].id;
            this.generateSplitItems();
        },
        handleOK: function () {
            var vm = this;
            var url = '/api/judge/' + this.sharedata.task_id + '/diffsegresults/' + this.diffsegresult_id + '/';
            var data = '';
            if (this.split_count == 1) {
                data = {
                    typ: 1,
                    split_info: '{}',
                    merged_diffsegresults: []
                }
            } else {
                var split_info = JSON.stringify({
                    split_count: this.split_count,
                    tripitaka_id_to_texts: this.tripitaka_id_to_texts,
                    selected_lst: this.selected_lst
                });
                data = {
                    typ: 2,
                    split_info: split_info,
                    selected: 1,
                    selected_text: this.selected_lst.join(''),
                    merged_diffsegresults: []
                }
            }
            
            axios.put(url, data)
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

Vue.component('show-split-dialog', {
    props: ['sharedata'],
    template: '\
    <el-dialog title="拆分" :visible.sync="sharedata.showSplitDialogVisible" width="50%" @open="handleOpen" :before-close="handleOK">\
        <table class="table table-bordered table-condensed">\
            <thead>\
                <tr>\
                    <th></th>\
                    <th v-for="tname in tname_lst">{{ tname }}</th>\
                    <th>我的选择</th>\
                </tr>\
            </thead>\
            <tbody>\
            <tr v-for="(title, index) in title_lst">\
                <td>{{ title }}</td>\
                <td v-for="(tripitaka_id, tripitaka_index) in tripitaka_ids">\
                {{ tripitaka_id_to_texts[tripitaka_id][index] }}\
                </td>\
                <td>\
                {{ selected_lst[index] }}\
                </td>\
            </tr>\
            </tbody>\
        </table>\
        <span slot="footer" class="dialog-footer">\
            <el-button type="primary" @click="handleOK">确定</el-button>\
        </span>\
    </el-dialog>\
    ',
    data: function () {
        return {
            split_count: 2,
            title_lst: [],
            tripitaka_ids: [],
            tname_lst: [],
            tripitaka_id_to_texts: {},
            selected_lst: []
        }
    },
    methods: {
        generateSplitItems: function() {
            var diffsegresult = this.sharedata.show_split_diffsegresult;
            if (diffsegresult.typ == 2) {
                var split_info = JSON.parse(diffsegresult.split_info);
                this.split_count = split_info.split_count;
                this.tripitaka_id_to_texts = split_info.tripitaka_id_to_texts;
                this.selected_lst = split_info.selected_lst;
                this.title_lst = [];
                this.tripitaka_ids = [];
                this.tname_lst = [];
                for (var i = 1; i <= this.split_count; ++i) {
                    this.title_lst.push(i.toString());
                }
                var diffsegtexts = diffsegresult.diffseg.diffsegtexts;
                var length = diffsegtexts.length;
                for (var i = 0; i < length; ++i) {
                    var tripitaka_id = diffsegtexts[i].tripitaka.id;
                    var tname = diffsegtexts[i].tripitaka.shortname;
                    this.tripitaka_ids.push(tripitaka_id);
                    this.tname_lst.push(tname);
                }
            }
        },
        handleOpen: function () {
            this.generateSplitItems();
        },
        handleOK: function () {
            this.sharedata.showSplitDialogVisible = false;
        },
        handleCancel: function() {
            this.sharedata.showSplitDialogVisible = false;
        }
    }
})

Vue.component('column-image', {
    props: ['imageinfo', 'sharedata'],
    template: '\
    <canvas class="columnimage" @click="handleClick"></canvas>\
    ',
    mounted: function() {
        this.updateImage();
    },
    watch: {
        imageinfo: function() {
            this.updateImage();
        }
    },
    methods: {
        updateImage: function() {
            var canvas = this.$el;
            var vm = this;
            var context = canvas.getContext("2d");
            var image = new Image();
            image.onload = function () {
                var width = 40;
                var height = width / image.width * image.height;
                console.log(image.width, image.height, width, height)
                canvas.width = width;
                canvas.height = height;
                context.clearRect(0, 0, width, height);
                context.drawImage(image, 0, 0, width, height);
                var xratio = width / image.width;
                var yratio = height / image.height;
                x = parseInt(vm.imageinfo.rect[0] * xratio);
                y = parseInt(vm.imageinfo.rect[1] * yratio);
                x1 = parseInt(vm.imageinfo.rect[2] * xratio);
                y1 = parseInt(vm.imageinfo.rect[3] * yratio);
                context.moveTo(x, y);
                context.lineTo(x1, y);
                context.lineTo(x1, y1);
                context.lineTo(x, y1);
                context.lineTo(x, y);
                //设置样式
                context.lineWidth = 1;
                context.strokeStyle = "#F5270B";
                //绘制
                context.stroke();
            };
            image.src = vm.imageinfo.url;
        },
        handleClick: function() {
            this.sharedata.pageDialogInfo = {
                page_url: this.imageinfo.page_url,
                start_char_pos: this.imageinfo.start_char_pos,
                end_char_pos: this.imageinfo.end_char_pos
            }
            this.sharedata.judgePageDialogVisible = true;
        }
    }
})

Vue.component('judge-image-dialog', {
    props: ['sharedata'],
    template: '\
    <el-dialog title="" :visible.sync="sharedata.judgeImageDialogVisible" width="50%" @open="handleOpen" :before-close="handleOK">\
        <table class="table table-condensed">\
            <tbody>\
            <tr>\
            <td v-for="(image, index) in images">{{ image.tname }}</td>\
            </tr>\
            <tr class="diffseg-image">\
            <td v-for="(image, index) in images"><column-image :imageinfo="image" :sharedata="sharedata"></column-image></td>\
            </tr>\
            <tr>\
            <td v-for="(image, index) in images"><b v-if="image.cross_line">...</b></td>\
            </tr>\
            </tbody>\
        </table>\
    </el-dialog>\
    ',
    data: function () {
        return {
            images: []
        }
    },
    methods: {
        generateItems: function(diffseg) {
            this.images = [];
            var image_url_prefix = this.sharedata.image_url_prefix;
            var tripitaka_info = this.sharedata.tripitaka_info;
            var diffsegtexts = diffseg.diffsegtexts;
            var length = diffsegtexts.length;
            for (var i = 0; i < length; ++i) {
                var tid = diffsegtexts[i].tripitaka.id;
                var tname = diffsegtexts[i].tripitaka.shortname;
                if (tname == 'CBETA') {
                    continue;
                }
                if (diffsegtexts[i].text == null) {
                    continue;
                }
                var cross_line = (diffsegtexts[i].start_char_pos.substr(0, 20) !=
                diffsegtexts[i].end_char_pos.substr(0, 20));
                this.images.push({
                    tid: tid,
                    tname: tname,
                    url: diffsegtexts[i].column_url,
                    page_url: diffsegtexts[i].page_url,
                    rect: diffsegtexts[i].rect,
                    start_char_pos: diffsegtexts[i].start_char_pos,
                    end_char_pos: diffsegtexts[i].end_char_pos,
                    cross_line: cross_line
                });
            }
        },
        handleOpen: function () {
            var vm = this;
            axios.get('/api/judge/' + vm.sharedata.task_id + '/diffsegs/' + vm.sharedata.image_diffseg_id + '/')
            .then(function(response) {
                var diffseg = response.data;
                vm.generateItems(diffseg);
            });
        },
        handleOK: function () {
            this.sharedata.judgeImageDialogVisible = false;
        }
    }
})

Vue.component('judge-page-dialog', {
    props: ['sharedata'],
    template: '\
    <el-dialog title="" :visible.sync="sharedata.judgePageDialogVisible" width="80%" @open="handleOpen" :before-close="handleOK">\
        <div class="row">\
            <div class="col-md-8">\
                <canvas id="page-canvas" width="800" height="1080"></canvas>\
            </div>\
            <div class="col-md-4">\
                <div class="judge-page-text" v-html="text"></div>\
            </div>\
        </div>\
    </el-dialog>\
    ',
    data: function () {
        return {
            text: ''
        }
    },
    methods: {
        clearImage: function() {
            try {
                var canvas = document.getElementById("page-canvas");
                var context = canvas.getContext("2d");
                context.clearRect(0, 0, canvas.width, canvas.height);
            } catch(err) {
            }
        },
        setImg: function(img_url, data, start_line_no, start_char_no, end_line_no, end_char_no) {
            //console.log('setImg: ', img_url)
            var canvas = document.getElementById("page-canvas");
            var context = canvas.getContext("2d");
            var image = new Image();
            image.onload = function () {
                var sx = 0;
                var sy = 0;
                var sw = canvas.width;
                var sh = canvas.height;
                if ('min_x' in data) {
                    sx = data['min_x'] - 130;
                    sy = data['min_y'] - 100;
                    sw = data['max_x'] + 130 - sx;
                    sh = data['max_y'] + 100 - sy;
                    if (data['min_y'] < data['max_y'] * 2 / 3) {
                        if (sy > 200) {
                            sy = 100;
                        }
                        sh = data['max_y'] + 100 - sy;
                    }
                }
                canvas.width = canvas.width;
                canvas.height = canvas.width / sw * sh;
                console.log(canvas.width, canvas.height)
                context.clearRect(0, 0, canvas.width, canvas.height);
                context.drawImage(image, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
                var xratio = canvas.width / sw;
                var yratio = canvas.height / sh;
                data['char_data'].forEach(function(v){
                    var line_no = v['line_no'];
                    var char_no = v['char_no'];
                    var color = "#F5270B";
                    var x = v['x'] - sx;
                    var y = v['y'] - sy;
                    var w = v['w'];
                    var h = v['h'];
                    x = parseInt(x * xratio);
                    y = parseInt(y * yratio);
                    w = parseInt(w * xratio);
                    h = parseInt(h * yratio);

                    var to_draw = false;
                    
                    if ('added' in v) {
                        color = 'ForestGreen';
                    } else if ('old_char' in v) {
                        color = 'blue';
                    }
                    if (start_line_no != end_line_no) {
                        if (line_no == start_line_no && char_no >= start_char_no) {
                            color = '#ff00ff';
                            to_draw = true;
                        } else if (line_no > start_line_no && line_no < end_line_no) {
                            color = '#ff00ff';
                            to_draw = true;
                        } else if (line_no == end_line_no && char_no <= end_char_no) {
                            color = '#ff00ff';
                            to_draw = true;
                        }
                    } else {
                        if (line_no == start_line_no && char_no >= start_char_no && 
                            char_no <= end_char_no) {
                            color = '#ff00ff';
                            to_draw = true;
                        }
                    }
                    if (to_draw) {
                        context.beginPath();
                        context.moveTo(x, y);
                        context.lineTo(x + w, y);
                        context.lineTo(x + w, y + h);
                        context.lineTo(x, y + h);
                        context.lineTo(x, y);
                        //设置样式
                        context.lineWidth = 1;
                        context.strokeStyle = color;
                        context.stroke();
                    }
                });
            };
            image.src = img_url;
        },
        loadImage: function() {
            var start_char_pos = this.sharedata.pageDialogInfo.start_char_pos;
            var end_char_pos = this.sharedata.pageDialogInfo.end_char_pos;
            var pid = start_char_pos.substr(0, 17);
            var start_line_no = parseInt(start_char_pos.substr(18, 2));
            var start_char_no = parseInt(start_char_pos.substr(21, 2));
            var end_line_no = parseInt(end_char_pos.substr(18, 2));
            var end_char_no = parseInt(end_char_pos.substr(21, 2));
            var cut_url = '/api/page/' + pid + '/';
            var vm = this;
            axios.get(cut_url).then(function(response) {
                var data = JSON.parse(response.data.cut_info);
                vm.text = vm.getDisplayHtml(response.data.text,
                    start_line_no, start_char_no, end_line_no, end_char_no);
                vm.setImg(vm.sharedata.pageDialogInfo.page_url, data,
                    start_line_no, start_char_no, end_line_no, end_char_no);
            });
        },
        getDisplayHtml: function(text, start_line_no, start_char_no, end_line_no, end_char_no) {
            var lines = text.split('\n');
            var text_lst = [];
            for (var i = 0; i < lines.length; ++i) {
                var line_no = i + 1;
                if (line_no < start_line_no) {
                    text_lst.push(lines[i]);
                    text_lst.push('<br />');
                } else if (line_no == start_line_no) {
                    if (start_char_no != 1) {
                        text_lst.push(lines[i].substr(0, start_char_no-1));
                    }
                    text_lst.push('<span class="judge-page-text-focus">');
                    if (start_line_no == end_line_no) {
                        var focus_length = end_char_no + 1 - start_char_no;
                        text_lst.push(lines[i].substr(start_char_no-1, focus_length));
                        text_lst.push('</span>');
                        if (end_char_no == lines[i].length) {
                            text_lst.push('<br />');
                        } else {
                            text_lst.push(lines[i].substr(end_char_no));
                            text_lst.push('<br />');
                        }
                    } else {
                        text_lst.push(lines[i].substr(start_char_no-1));
                        text_lst.push('<br />');
                    }
                } else if (line_no > start_line_no && line_no < end_line_no) {
                    text_lst.push(lines[i]);
                    text_lst.push('<br />');
                } else if (line_no == end_line_no) {
                    text_lst.push(lines[i].substr(0, end_char_no));
                    text_lst.push('</span>');
                    if (end_char_no == lines[i].length) {
                        text_lst.push('<br />');
                    } else {
                        text_lst.push(lines[i].substr(end_char_no));
                        text_lst.push('<br />');
                    }
                } else {
                    text_lst.push(lines[i]);
                    text_lst.push('<br />');
                }
            }
            var html = text_lst.join('');
            return html;
        },
        handleOpen: function () {
            this.clearImage();
            this.text = '';
            this.loadImage();
        },
        handleOK: function () {
            this.sharedata.judgePageDialogVisible = false;
        }
    }
})
