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

function judge_get_seg_list(text, diffseg_pos_lst, id_key) {
    var seg_list = [];
    var i = 0;
    var diffseg_idx = 0;
    while (i < text.length) {
        if (diffseg_idx < diffseg_pos_lst.length) {
            var pos = diffseg_pos_lst[diffseg_idx].base_pos;
            var length = diffseg_pos_lst[diffseg_idx].base_length;
            if (i < pos) {
                seg_list.push({
                    'text': text.substr(i, pos-i),
                    'position': i
                })
                i = pos;
            }
            var obj = {
                'text': text.substr(i, length),
                'position': i
            }
            obj[id_key] = diffseg_pos_lst[diffseg_idx][id_key];
            seg_list.push(obj);
            i = pos + length;
            ++diffseg_idx;
        } else {
            seg_list.push({
                'text': text.substr(i),
                'position': i
            })
            i = text.length;
        }
    }
    return seg_list;
}

function merge_text_punct(text, puncts) {
    var result = [];
    var i = 0;
    puncts.forEach(function(punct) {
        if (i < punct[0]) {
            result.push(text.substr(i, punct[0] - i));
        }
        var p_text = punct[1];
        if (p_text == '\n') {
            p_text = '<br />';
        }
        result.push(p_text);
        i = punct[0];
    });
    if (i < text.length) {
        result.push(text.substr(i));
    }
    return result.join('');
}

function judge_merge_text_punct(text, diffseg_pos_lst, id_key, punct_lst) {
    var seg_list = judge_get_seg_list(text, diffseg_pos_lst, id_key);
    var punct_idx = 0;
    var start_pos = 0;
    var end_pos = 0;
    seg_list.forEach(function (seg) {
        end_pos = start_pos + seg.text.length;
        // 添加标点
        var punct_end_pos = end_pos;
        if (id_key in seg) {
            punct_end_pos = end_pos - 1;
        }
        var puncts = [];
        while (punct_idx < punct_lst.length) {
            var punct_pos = punct_lst[punct_idx][0];
            var punct_ch = punct_lst[punct_idx][1];
            if (punct_pos <= punct_end_pos) {
                puncts.push([punct_pos - start_pos, punct_ch]);
                ++punct_idx;
            } else {
                break;
            }
        }
        if (puncts.length > 0) {
            seg.text = merge_text_punct(seg.text, puncts);
        }
        start_pos = end_pos;
    });
    return seg_list;
}

// judge
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

Vue.component('diffseg-box', {
    props: ['diffsegresult', 'segindex', 'sharedata'],
    template: `
    <div :class="currentKls" @click.stop.prevent="click">
        <div>
            <span v-if="diffsegresult.selected_text == null" ><font style="background:white;color:red;font-size:20px;">{{ base_text }}</font></span>
            <span v-else ><font style="background:white;color:green;font-size:20px;">{{ base_text }}</font></span>
            <span><a href="#" @click.stop.prevent="showImage(diffsegresult)" style="text-decoration:underline;">查看列图</a></span>
        </div>

        <span v-for="(diffsegtexts, text, index) in diffsegresult.text_to_diffsegtexts">
            <span v-for="(diffsegtext, idx) in diffsegtexts">
                <span v-if="idx != 0">/</span><a href="#" @click="openPageDialog(diffsegtext)" style="text-decoration:underline;">{{ diffsegtext.tripitaka.shortname }}</a>
            </span>
            <span v-if="text">：{{ text }}</span>
            <span v-else>：为空</span>
            <span v-if="index < (diffsegresult.text_count - 1)">；</span>
            <span v-else>。</span>
        </span>

        <div v-if="sharedata.task_typ != 3" v-for="(judge_result, index) in diffsegresult.judge_results">
            <div>
                <span>判取{{ index + 1 }}：{{ getResult(judge_result) }}</span>
                <a href="#" v-if="judge_result.typ == 2" @click.stop.prevent="showSplit(judge_result)">显示拆分方案</a>
            </div>
        </div>
        <div v-if="sharedata.judge_verify_task_id != 0">
            <div>
                <span style="line-height:50px!important;">判取审定：{{ getResult(diffsegresult.judge_verify_result) }}</span>
                <a href="#" v-if="diffsegresult.judge_verify_result.typ == 2" @click.stop.prevent="showSplit(diffsegresult.judge_verify_result)">显示拆分方案</a>
            </div>
        </div>
        <div>
            <a href="#" class="diffseg-btn" @click.stop.prevent="doJudge(segindex)" :disabled="diffsegresult.typ == 2">判取</a>
            <a href="#" class="diffseg-btn" @click.stop.prevent="doMerge(segindex)" :disabled="diffsegresult.typ == 2">合并</a>
            <a href="#" class="diffseg-btn" v-if="base_text.length > 1" @click.stop.prevent="doSplit(segindex)">拆分</a>
        </div>
        <div>
            <span v-if="diffsegresult.selected_text != null" style="background:#eee;">处理结果：{{ getResult(diffsegresult, (sharedata.task_typ != 12)) }}</span>
        </div>
    </div>`,
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
        },
        currentKls: function() {
            if (this.sharedata.diffseg_id == this.diffsegresult.diffseg.id) {
                return 'diffseg-box selected-box';
            }
            else {
                return 'diffseg-box';
            }
        }
    },
    methods: {
        jumptodiffseg: function(diffseg_id) {
            try {
              if (!$('a[diffsegid='+ diffseg_id + ']')) {
                return
              }
              $('a[diffsegid='+ diffseg_id + ']').focus()
              var offset = $('#judge-base-text').scrollTop() + $('a[diffsegid='+ diffseg_id + ']')[0].getBoundingClientRect().top - 360;
              $('#judge-base-text').scrollTop = offset;
            } catch(err) {
              console.log('jumptodiffseg: ', err)
            }
        },

        click: function() {
            this.sharedata.diffseg_id = this.diffsegresult.diffseg.id;
            this.jumptodiffseg(this.sharedata.diffseg_id)

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
            if (this.diffsegresult.typ == 2) {
                return ;
            }
            this.sharedata.segindex = segindex;
            this.sharedata.mergeDialogVisible = true;
        },
        doSplit: function(segindex) {

            this.sharedata.segindex = segindex;
            this.sharedata.splitDialogVisible = true;
        },
        getResult: function(diffsegresult, enable_doubt=true) {
            var s = '';
            if (diffsegresult.selected == 0) {
                s += '未判取。';
            } else if (!enable_doubt || diffsegresult.doubt == 0) {
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
    template: `
    <span v-if="data.diffseg_id == undefined" v-html="data.text" style="font-size:20;"></span>
    <span v-else-if="data.text.length == 0"><a href="#" :diffsegid="data.diffseg_id" :class="className" :tabindex="data.diffseg_id" style="text-decoration:none;font-size:20;" @click="choiceThis()" v-html="selected_text" @keydown="keyDown($event)"></a></span>
    <span v-else><a href="#" :diffsegid="data.diffseg_id" :class="className" :tabindex="data.diffseg_id" style="text-decoration:none;font-size:20;" @click="choiceThis()" v-html="selected_text"  @keydown="keyDown($event)"></a></span>
    `,
    computed: {

        className: function() {

            if (this.data.diffseg_id != undefined) {
                if (this.data.text.length == 0) {
                    if (this.sharedata.diffseg_id == this.data.diffseg_id) {

                        for (var diffseg in this.sharedata.result_marked_list){
                            if (this.data.diffseg_id == this.sharedata.result_marked_list[diffseg].diffseg_id){
                                if (this.sharedata.result_marked_list[diffseg].marked == true){
                                    return 'diffseg-tag-selected-judged';
                                }else {
                                    return 'diffseg-tag-selected-notext';
                                }
                                break;
                            }

                        }
                        return 'diffseg-tag-notext-selected';

                    } else {
                        for (var diffseg in this.sharedata.result_marked_list){
                            if (this.data.diffseg_id == this.sharedata.result_marked_list[diffseg].diffseg_id){
                                if (this.sharedata.result_marked_list[diffseg].marked == true){
                                    return 'diffseg-tag-judged-none';
                                }else {
                                    return 'diffseg-tag-notext';
                                }
                                break;
                            }

                        }
                        return 'diffseg-tag-notext';

                    }
                } else {
                    if (this.sharedata.diffseg_id == this.data.diffseg_id) {
                        for (var diffseg in this.sharedata.result_marked_list){
                            if (this.data.diffseg_id == this.sharedata.result_marked_list[diffseg].diffseg_id){
                                if (this.sharedata.result_marked_list[diffseg].marked == true){
                                    return 'diffseg-tag-selected-judged';
                                }else {
                                    return 'diffseg-tag-selected-notext';
                                }
                                break;
                            }

                        }
                    } else {
                        for (var diffseg in this.sharedata.result_marked_list){
                            if (this.data.diffseg_id == this.sharedata.result_marked_list[diffseg].diffseg_id){
                                if (this.sharedata.result_marked_list[diffseg].marked == true){
                                    return 'diffseg-tag-judged';
                                }else {
                                    break;
                                }
                                break;
                            }

                        }

                    }

                }

            }
            return '';
        },
        selected_text: function(){
            var s = '';
            for (var diffseg in this.sharedata.result_marked_list){
                if (this.data.diffseg_id == this.sharedata.result_marked_list[diffseg].diffseg_id){
                    if (this.sharedata.result_marked_list[diffseg].selected_text.length == 0){
                        s += this.data.text;
                    }else{
                        s += this.sharedata.result_marked_list[diffseg].selected_text;
                    }
                    break;
                }

            }
            return s;
        }
    },
    methods: {
        choiceThis: function() {
            this.sharedata.diffseg_id = this.data.diffseg_id;
            this.sharedata.image_diffseg_id = this.data.diffseg_id;
            let idx = _.findIndex(this.sharedata.diffseg_pos_lst, function(v) {return v.diffseg_id == this.data.diffseg_id}.bind(this))
            this.$emit('diffpage', parseInt(idx/5)+1)

            //this.sharedata.judgeImageDialogVisible = true;
        },
        keyDown(e) {
            if(e && e.keyCode==27){ // 按 Esc
                //要做的事情
            }
            if(e && e.keyCode==113){ // 按 F2
                //要做的事情
            }
            if(e && e.keyCode==13){ // enter 键
                //要做的事情
            }
            if(e && e.keyCode==9){ // tab 键
                diffseg_id = this.data.diffseg_id + 1;
                this.sharedata.diffseg_id = diffseg_id;
                this.sharedata.image_diffseg_id = diffseg_id;
                let idx = _.findIndex(this.sharedata.diffseg_pos_lst, function(v) {return v.diffseg_id == diffseg_id}.bind(this))
                this.$emit('diffpage', parseInt(idx/5)+1)
            }
        },
        mounted() {
            document.body.onkeydown = this.keyDown;
        },
    }
})

Vue.component('judge-dialog', {
    props: ['sharedata'],
    template: `
    <el-dialog title="判取" :visible.sync="sharedata.judgeDialogVisible" width="30%" @open="handleOpen" :before-close="handleCancel">
        <table class="table table-bordered">
            <thead>
            <tr><th>判取</th><th>版本</th><th>用字</th></tr>
            </thead>
            <tbody v-if="sharedata.segindex >= 0">
            <tr v-for="(diffsegtexts, text) in sharedata.diffsegresults[sharedata.segindex].text_to_diffsegtexts">
                <td>
                    <input type="radio" v-bind:value="text" v-model="selected_text" />
                </td>
                <td>{{ joinTnames(diffsegtexts) }}</td>
                <td>{{ text }}</td>
            </tr>
            </tbody>
        </table>
        <div v-if="sharedata.task_typ != 12">
            <span>是否存疑：</span>
            <div class="radio"><label>
                <input type="radio" v-model="doubt" value="0" />否
            </label></div>
            <div class="radio"><label>
                <input type="radio" v-model="doubt" value="1" />是
            </label></div>
            <div v-show="doubt == 1">
                <div>存疑说明：</div>
                <textarea class="form-control" rows="3" v-model="doubt_comment"></textarea>
            </div>
        </div>
        <span slot="footer" class="dialog-footer">
            <span class="alert alert-danger" v-if="error">{{ error }}</span>
            <el-button type="primary" :disabled="sharedata.permit_modify" @click="handleOK">确定</el-button>
            <el-button @click="handleCancel">取消</el-button>
        </span>
    </el-dialog>
    `,
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
            if (this.sharedata.task_typ != 12) {
                this.doubt = this.sharedata.diffsegresults[this.sharedata.segindex].doubt;
                this.doubt_comment = this.sharedata.diffsegresults[this.sharedata.segindex].doubt_comment;
            }
        },
        handleOK: function() {
            var vm = this;
            var url = '/api/judge/' + this.sharedata.task_id + '/diffsegresults/' + this.diffsegresult_id + '/';
            var data = {
                typ: 1,
                selected_text: this.selected_text,
                selected: 1,
                split_info: '{}'
            }
            if (this.sharedata.task_typ != 12) {
                data.doubt = this.doubt;
                data.doubt_comment = this.doubt_comment;
            }

            // this.reloaddiffseg(this.diffsegresult_id);
            //
            axios.put(url, data)
            .then(function(response) {
                vm.sharedata.diffsegresults[vm.sharedata.segindex].selected_text = vm.selected_text;
                vm.sharedata.diffsegresults[vm.sharedata.segindex].selected = vm.selected;
                vm.sharedata.diffsegresults[vm.sharedata.segindex].doubt = vm.doubt;
                vm.sharedata.diffsegresults[vm.sharedata.segindex].doubt_comment = vm.doubt_comment;
                //更新判取数据
                for (var diffseg in vm.sharedata.result_marked_list){
                    if (vm.sharedata.diffsegresults[vm.sharedata.segindex].diffseg.id == vm.sharedata.result_marked_list[diffseg].diffseg_id){
                        if (vm.selected_text.length == 0){
                            vm.sharedata.result_marked_list[diffseg].selected_text = '';
                            vm.sharedata.result_marked_list[diffseg].marked = true;
                        }else {
                            vm.sharedata.result_marked_list[diffseg].selected_text = vm.selected_text;
                            vm.sharedata.result_marked_list[diffseg].marked = true;
                        }
                        break;
                    }
                }
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
    template: `
    <el-dialog title="合并" :visible.sync="sharedata.mergeDialogVisible" width="30%" @open="handleOpen" :before-close="handleCancel">
        <p>选择待合并的校勘记</p>
        <ul>
            <li v-for="diffsegresult in diffsegresults">
            <input type="checkbox" :id="diffsegresult.id" :value="diffsegresult.id" v-model="diffsegresult_ids" />
            <label :for="diffsegresult.id">{{ getBaseText(diffsegresult) }}</label>
            </li>
        </ul>
        <span slot="footer" class="dialog-footer">
            <span class="alert alert-danger" v-if="error">{{ error }}</span>
            <el-button type="primary" :disabled="sharedata.permit_modify" @click="handleOK">合并</el-button>
            <el-button @click="handleCancel">取消</el-button>
        </span>
    </el-dialog>
    `,
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
            merged_diffsegresults.push(this.diffsegresult_id);
            let new_results = _.sortedUniq(merged_diffsegresults);
            new_results.sort();
            
            for (let n =1;  n< new_results.length; n++) {
                if (new_results[n] - new_results[n-1] != 1)
                {
                    alert('请选择连续段合并。')
                    return;
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
    template: `
    <el-dialog title="拆分" :visible.sync="sharedata.splitDialogVisible" :width="split_width" @open="handleOpen" :before-close="handleCancel">
        <button class="btn" @click="incrementSplitCount" style="margin: 0 4px 4px 0;">新增</button>
        <button class="btn" @click="decrementSplitCount" style="margin: 0 4px 4px 0;">减少</button>
        
        <table class="table table-bordered table-condensed">
            <thead>
                <tr >
                    <th style="text-align:center;"></th>
                    <th v-for="tname in tname_lst" style="text-align:center;">{{ tname }}</th>
                    <th style="text-align:center;">我的选择</th>
                </tr>
            </thead>
            <tbody>
            <tr v-for="(title, index) in title_lst">
                <td align="center">{{ title }}</td>
                <td v-for="(tripitaka_id, tripitaka_index) in tripitaka_ids" align="center">
                    <textarea cols="4" v-model="tripitaka_id_to_texts[tripitaka_id][index]" @input="verifyData"></textarea>
                </td>
                <td align="center">
                    <textarea cols="4" v-model="selected_lst[index]" @input="verifyData"></textarea>
                </td>
            </tr>
            </tbody>
        </table>
        <span slot="footer" class="dialog-footer">
            <span class="alert alert-danger" v-if="error">{{ error }}</span>
            <el-button type="primary" @click="handleOK" :disabled="sharedata.permit_modify && okDisabled">确定</el-button>
            <el-button @click="handleCancel">取消</el-button>
        </span>
    </el-dialog>
    `,
    data: function () {
        return {
            diffsegresult_id: '',
            split_count: 2,         //拆分总数
            split_count_old:2,      //拆分总数-原值
            diffseg_id_old:-1,         //待处理文字编号-原值
            is_init:1,              //是否为初始化：1是0否。
            title_lst: [],          //类别名称：1、2、3等
            // split_text_list:[],     //拆分后的数据按列表存储
            tripitaka_ids: [],      //藏经id
            tname_lst: [],          //藏经名称:永北、乾隆、高丽等 
            tripitaka_id_to_oldtext: {},//返回的拆分数据原值
            tripitaka_id_to_texts: {},  //生成的拆分数据
            selected_lst: [],           //我的选择中拆分数据
            okDisabled: true,
            error: null
        }
    },
    computed: {
        split_width: function(){
            //初始化页面宽度
            return (this.tname_lst.length+1)*150+"px";
        },
        
    },
    methods: {
        splitText: function(text, count) {
            var textseg_lst = [];
            if (!text) {
                return textseg_lst
            }
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
            //根据待处理文字的id，判断是否切换了待处理文字，如果是，标记为待初始化。
            if (this.sharedata.diffsegresults[this.sharedata.segindex].id != this.diffseg_id_old){
                this.is_init = 1;
                this.diffseg_id_old = this.sharedata.diffsegresults[this.sharedata.segindex].id;
                this.split_count = 2;
                this.split_count_old = this.split_count;
            }
            //准备空数据，用来更新拆分框的内容。
            this.title_lst = [];
            this.tripitaka_ids = [];
            this.tname_lst = [];
            this.tripitaka_id_to_oldtext = {};
            console.log(diffsegresult.typ);
            //开始处理
            if (diffsegresult.typ == 2) {
                var split_info = JSON.parse(diffsegresult.split_info);
                
                //获取当前校勘文字的返回数据
                var diffsegtexts = this.sharedata.diffsegresults[this.sharedata.segindex].diffseg.diffsegtexts;
                var length = diffsegtexts.length;
                
                //开始计算
                for (var i = 0; i < length; ++i) {
                    //获取网页需要的数据
                    if (diffsegtexts[i].text != null){
                        // var text_lst = this.splitText(diffsegtexts[i].text, this.split_count);
                        var tripitaka_id = diffsegtexts[i].tripitaka.id;
                        
                        if (this.is_init == 1){//初始化
                            //获取返回的拆分总数
                            this.split_count = split_info.split_count;
                            //获取返回的拆分信息
                            var text_lst = split_info.tripitaka_id_to_texts[tripitaka_id];
                            //将网络返回的拆分数据作为初始化的值
                            this.tripitaka_id_to_texts = split_info.tripitaka_id_to_texts;
                            this.selected_lst = split_info.selected_lst;
                           
                        }else if (this.split_count > this.split_count_old){//当增加时
                            //保留原始的拆分数据
                            var text_lst = this.tripitaka_id_to_texts[tripitaka_id];
                        }else if (this.split_count < this.split_count_old){//当减少时
                            //末尾两项合并，删除最后一行。
                            var text_lst = this.tripitaka_id_to_texts[tripitaka_id];
                            if (text_lst == null){
                                //正常
                                text_lst = [];
                            }else{
                                len = this.split_count_old;
                                //修改原始的拆分数据
                                if (len > 1) {
                                    if (text_lst[len-1] == NaN || text_lst[len-1] == undefined || text_lst[len-1] == 'undefined'){
                                        text_lst[len-1] = '';
                                    }
                                    if (text_lst[len-2] == NaN || text_lst[len-2] == undefined || text_lst[len-2] == 'undefined'){
                                        text_lst[len-2] = '';
                                    }
                                    text_lst[len-2]=text_lst[len-2]+text_lst[len-1];
                                    text_lst.splice(len-1);
                                    
                                }
                            }
                        }else if (this.split_count == this.split_count_old){//当不变时
                            //保留原始的拆分数据
                            var text_lst = this.tripitaka_id_to_texts[tripitaka_id];
                        }
                        //填充拆分框内数据
                        var tname = diffsegtexts[i].tripitaka.shortname;
                        this.tripitaka_ids.push(tripitaka_id);
                        this.tname_lst.push(tname);
                        this.tripitaka_id_to_oldtext[tripitaka_id] = diffsegtexts[i].text;
                        for (var j = 0; j < text_lst.length; ++j){
                            if (text_lst[j] == NaN || text_lst[j] == undefined || text_lst[j] == 'undefined'){
                                text_lst[j] = '';
                            }
                        }
                        //当拆分数据长度小于split_count时，后面用''填充。
                        var count = text_lst.length;
                        for (var k = 0;k < this.split_count-count;k++){
                            text_lst.push('');
                            console.log(tripitaka_id+'--'+text_lst);
                        }
                        this.tripitaka_id_to_texts[tripitaka_id] = text_lst;
                    }else{//当没有该藏经数据时，将其值设置为''.
                        var tripitaka_id = diffsegtexts[i].tripitaka.id;
                        this.tripitaka_id_to_texts[tripitaka_id] = '';
                    }
                    
                }
                
                //生成拆分框的行号
                for (var i = 1; i <= this.split_count; ++i) {
                    this.title_lst.push(i.toString());
                }
                //处理“我的选择”数据
                if (this.is_init == 1){//初始化
                    //关闭初始化
                    this.is_init = 0;
                    this.split_count_old = this.split_count;
                }else if (this.split_count > this.split_count_old){//当增加时
                    //保留原始的拆分数据
                    this.selected_lst[this.split_count-1] = '';
                    
                }else if (this.split_count < this.split_count_old){//当减少时
                    if (this.selected_lst[this.split_count-1] == NaN || this.selected_lst[this.split_count-1] == undefined ||this.selected_lst[this.split_count-1] == 'undefined'){
                        this.selected_lst[this.split_count-1] = '';
                    }
                    if (this.selected_lst[this.split_count] == NaN || this.selected_lst[this.split_count] == undefined ||this.selected_lst[this.split_count] == 'undefined' ){
                        this.selected_lst[this.split_count] = '';
                    }
                    this.selected_lst[this.split_count-1] = this.selected_lst[this.split_count-1]+this.selected_lst[this.split_count];
                    this.selected_lst.splice(this.split_count);
                    
                }else if (this.split_count == this.split_count_old){//当不变时
                    //保留原始的拆分数据
                }
                
            } else {
                if (this.tripitaka_id_to_texts.length == 0){
                    this.tripitaka_id_to_texts = {};//当尚未进行拆分时
                }
                this.selected_lst = [];
                for (var i = 1; i <= this.split_count; ++i) {
                    this.title_lst.push(i.toString());
                    this.selected_lst.push('');
                }
                var diffsegtexts = this.sharedata.diffsegresults[this.sharedata.segindex].diffseg.diffsegtexts;
                var length = diffsegtexts.length;
                //开始计算
                for (var i = 0; i < length; ++i) {
                    //获取网页需要的数据
                    if (diffsegtexts[i].text != null){
                        // var text_lst = this.splitText(diffsegtexts[i].text, this.split_count);
                        var tripitaka_id = diffsegtexts[i].tripitaka.id;
                        if (this.is_init == 1){//初始化
                            //获取返回的拆分信息
                            var text_lst = this.splitText(diffsegtexts[i].text, this.split_count);
                            this.selected_lst = [];
                            this.tripitaka_id_to_texts[tripitaka_id] = text_lst;
                           
                        }else if (this.split_count > this.split_count_old){//当增加时
                            //保留原始的拆分数据
                            if (this.tripitaka_id_to_texts[tripitaka_id] == undefined){
                                var text_lst = [];
                            }else{
                                var text_lst = this.tripitaka_id_to_texts[tripitaka_id];
                            }
                        }else if (this.split_count < this.split_count_old){//当减少时
                            //末尾两项合并，删除最后一行。
                            var text_lst = this.tripitaka_id_to_texts[tripitaka_id];
                            if (text_lst == null){
                                //正常
                                text_lst = [];
                            }else {
                                len = this.split_count_old;
                                //修改原始的拆分数据
                                if (len > 1) {
                                    if (text_lst[len-1] == NaN || text_lst[len-1] == undefined || text_lst[len-1] == 'undefined'){
                                        text_lst[len-1] = '';
                                    }
                                    if (text_lst[len-2] == NaN || text_lst[len-2] == undefined || text_lst[len-2] == 'undefined'){
                                        text_lst[len-2] = '';
                                    }
                                    text_lst[len-2]=text_lst[len-2]+text_lst[len-1];
                                    text_lst.splice(len-1);
                                    
                                }
                            }
                        }else if (this.split_count == this.split_count_old){//当不变时
                            //保留原始的拆分数据
                            var text_lst = this.tripitaka_id_to_texts[tripitaka_id];
                        }
                        var tname = diffsegtexts[i].tripitaka.shortname;
                        this.tripitaka_ids.push(tripitaka_id);
                        this.tname_lst.push(tname);
                        this.tripitaka_id_to_oldtext[tripitaka_id] = diffsegtexts[i].text;
                        for (var j = 0; j < text_lst.length; ++j){
                            if (text_lst[j] == NaN || text_lst[j] == undefined || text_lst[j] == 'undefined'){
                                text_lst[j] = '';
                            }
                        }
                        //当拆分数据长度小于split_count时，后面用''填充。
                        var count = text_lst.length;
                        for (var k = 0;k < this.split_count-count;k++){
                            text_lst.push('');
                        }
                        this.tripitaka_id_to_texts[tripitaka_id] = text_lst;
                    }else{//当没有该藏经数据时，将其值设置为''.
                        var tripitaka_id = diffsegtexts[i].tripitaka.id;
                        this.tripitaka_id_to_texts[tripitaka_id] = '';
                    }
                    
                }
                //处理“我的选择”数据
                if (this.is_init == 1){//初始化
                    //关闭初始化
                    this.is_init = 0;
                    this.split_count_old = this.split_count;
                }else if (this.split_count > this.split_count_old){//当增加时
                    //保留原始的拆分数据
                    this.selected_lst[this.split_count-1] = '';
                    
                }else if (this.split_count < this.split_count_old){//当减少时
                    if (this.selected_lst[this.split_count-1] == NaN || this.selected_lst[this.split_count-1] == undefined ||this.selected_lst[this.split_count-1] == 'undefined'){
                        this.selected_lst[this.split_count-1] = '';
                    }
                    if (this.selected_lst[this.split_count] == NaN || this.selected_lst[this.split_count] == undefined ||this.selected_lst[this.split_count] == 'undefined' ){
                        this.selected_lst[this.split_count] = '';
                    }
                    this.selected_lst[this.split_count-1] = this.selected_lst[this.split_count-1]+this.selected_lst[this.split_count];
                    this.selected_lst.splice(this.split_count);
                    
                }else if (this.split_count == this.split_count_old){//当不变时
                   //不做处理
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
            this.split_count_old = this.split_count;
            if (this.split_count < 20) {
                this.split_count++;
                this.generateSplitItems();
            }
        },
        decrementSplitCount: function () {
            this.split_count_old = this.split_count;
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
            this.diffsegresult_id = this.sharedata.diffsegresults[this.sharedata.segindex].id;
            var vm = this;
            var url = '/api/judge/' + this.sharedata.task_id + '/diffsegresults/' + this.diffsegresult_id + '/';
            var data = '';
            if (this.split_count == 1) {
                data = {
                    typ: 2,
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
            //判断拆分数据中是否包含整行均为空的数据，如果包含，进行提示。
            var arr = this.tripitaka_id_to_texts;
            var result_arr = [];
            for (var item in arr){
                var text_lst = arr[item];
                for (var j in text_lst){
                    if (text_lst[j] == ''){
                        if (result_arr[j] == null){
                            result_arr[j] = 1;
                        }else{
                            result_arr[j] = result_arr[j]+1;
                        }
                        
                    }
                }
            }
            var put_flag = 1;
            for (var k in result_arr){
                if (result_arr[k] == this.tripitaka_ids.length){
                    var line = parseInt(k)+1;
                    vm.error = '第'+line+'行不能为空';
                    put_flag = 0;
                    break;
                }
            }
            if (put_flag == 1){
                axios.put(url, data)
                .then(function(response) {
                    vm.$emit('reload');
                    vm.sharedata.splitDialogVisible = false;
                    //页面关闭，还原为待初始化状态。
                    this.is_init = 0;
                    this.split_count_old = this.split_count;
                    //清除错误提示
                    vm.error = null;
                })
                .catch(function (error) {
                    if (error.data.non_field_errors[0] != null){
                        
                        if (error.data.non_field_errors[0] == 'invalid split_info:oldtext not equal texts.'){
                            vm.error = '提交数据与原始经文不符。';
                        }else if (error.data.non_field_errors[0] == 'invalid split_info：texts length not equal split_count.'){
                            vm.error = '经文拆分结果异常。';
                        }else if (error.data.non_field_errors[0] == 'invalid split_info:selected_text not equal selected_lst.'){
                            vm.error = '拆分数据和选择数据不符。';
                        }else if (error.data.non_field_errors[0] == 'invalid split_info:split_info not have selected_lst'){
                            vm.error = '缺少“我的选择”数据。';
                        }else if (error.data.non_field_errors[0] == 'no selected_text'){
                            vm.error = '拆分数至少为2。';
                        }else{
                            vm.error = error.data.non_field_errors[0];
                        }
                    }else{
                        vm.error = '提交出错！';
                    }
                });
            }
        },
        handleCancel: function() {
            this.sharedata.splitDialogVisible = false;
            this.error = null;
            //页面关闭，还原为待初始化状态。
            this.is_init = 0;
            this.split_count_old = this.split_count;
            this.error = null;
        }
    }
})

Vue.component('show-split-dialog', {
    props: ['sharedata'],
    template: `
    <el-dialog title="拆分" :visible.sync="sharedata.showSplitDialogVisible" width="50%" @open="handleOpen" :before-close="handleOK">
        <table class="table table-bordered table-condensed">
            <thead>
                <tr>
                    <th></th>
                    <th v-for="tname in tname_lst">{{ tname }}</th>
                    <th>我的选择</th>
                </tr>
            </thead>
            <tbody>
            <tr v-for="(title, index) in title_lst">
                <td>{{ title }}</td>
                <td v-for="(tripitaka_id, tripitaka_index) in tripitaka_ids">
                {{ tripitaka_id_to_texts[tripitaka_id][index] }}
                </td>
                <td>
                {{ selected_lst[index] }}
                </td>
            </tr>
            </tbody>
        </table>
        <span slot="footer" class="dialog-footer">
            <el-button type="primary" :disabled="sharedata.permit_modify" @click="handleOK">确定</el-button>
        </span>
    </el-dialog>
    `,
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
                var width = 80;
                var height = width / image.width * image.height;
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
                if (vm.imageinfo.text == '') {
                    y1 = y;
                }
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
    template: `
    <el-dialog title="" :visible.sync="sharedata.judgeImageDialogVisible" :width="images_width" @open="handleOpen" :before-close="handleOK">
    <table class="table table-condensed">
            <tbody>
            <tr>
            <td v-for="(image, index) in images" align="center" style="font-size:20;">{{ image.tname }}</td>
            </tr>
            <tr class="diffseg-image">
            <td v-for="(image, index) in images" align="center"><column-image :imageinfo="image" :sharedata="sharedata"></column-image></td>
            </tr>
            <tr>
            <td v-for="(image, index) in images" align="center"><b v-if="image.cross_line">...</b></td>
            </tr>
            </tbody>
        </table>
    </el-dialog>
    `,
    data: function () {
        return {
            images: []
        }
    },
    computed: {
        images_width: function() {
            return this.images.length *(80+30) + 20 + "px";
        },
    },
    methods: {
        generateItems: function(diffseg) {
            this.images = [];
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
                if (diffsegtexts[i].column_url == null) {
                    continue;
                }
                this.images.push({
                    tid: tid,
                    tname: tname,
                    text: diffsegtexts[i].text,
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
    template: `
    <el-dialog title="" :visible.sync="sharedata.judgePageDialogVisible" width="95%" height="95%" top="2vh" @open="handleOpen" :before-close="handleOK">
        <div class="row" >
            <div class="col-md-8 canvas-wrapper" id="canvasWrapper">
                <canvas id="page-canvas" width="800"  ></canvas>
            </div>
            <div class="col-md-4 text-wrapper" style="background:white;">
                <div class="judge-page-text" v-html="text" style="background:white;"></div>
            </div>
        </div>
    </el-dialog>
    `,
    data: function () {
        return {
            text: '',
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
            var canvas = document.getElementById("page-canvas");
            var context = canvas.getContext("2d");
            var image = new Image();
            image.onload = function () {
                var sx = 0;
                var sy = 0;
                var sw = image.width;
                var sh = image.height;
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
                canvas.width = image.width;
                canvas.height = image.height ;/// sw * sh;

                context.clearRect(0, 0, canvas.width, canvas.height);
                context.drawImage(image, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
                var xratio = canvas.width / sw;
                var yratio = canvas.height / sh;
                data['char_data'].forEach(function(v){
                    var line_no = v['line_no'];
                    var char_no = v['char_no'];
                    var color = "red";// "#F5270B";
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
                            // color = '#ff00ff';
                            color = 'red';
                            to_draw = true;
                        } else if (line_no > start_line_no && line_no < end_line_no) {
                            // color = '#ff00ff';
                            color = 'red';
                            to_draw = true;
                        } else if (line_no == end_line_no && char_no <= end_char_no) {
                            // color = '#ff00ff';
                            color = 'red';
                            to_draw = true;
                        }
                    } else {
                        if (line_no == start_line_no && char_no >= start_char_no &&
                            char_no <= end_char_no) {
                            // color = '#ff00ff';
                            color = 'red';
                            to_draw = true;
                        }
                    }
                    //动态调整图片框高度
                    document.getElementById('canvasWrapper').style.height=image.height+20+"px";//页面初始化
                    
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
});
Vue.component('correct-feedback-dialog', {
    props: ['sharedata'],
    template: `
    <el-dialog title="校对文字反馈" :visible.sync="sharedata.correctFeedbackDialogVisible" width="35%" @open="handleOpen" :before-close="handleCancel">
        <div class="row">
        现有文本:<p>{{ sharedata.original_text }}</p>
        反馈文本：<el-input v-model="sharedata.fb_text"></el-input>
        反馈意见：<el-input v-model="sharedata.fb_comment"></el-input>
            <span slot="footer" class="dialog-footer">
                <span class="alert alert-danger" v-if="error">{{ error }}</span>
                <el-button type="primary" @click="handleOK">确定</el-button>
                <el-button @click="handleCancel">取消</el-button>
            </span>
        </div>
    </el-dialog>
    `,
    data: function () {
        return {
            error: null,
        }
    },
    methods: {
        handleOpen: function () {
        },
        handleOK: function () {
            var vm = this;
            axios.post('/api/correctfeedback/', {
                'position': this.sharedata.selection_start,
                'fb_text': this.sharedata.fb_text,
                'fb_comment': this.sharedata.fb_comment,
                'correct_text': this.sharedata.reelcorrectid,
                'original_text': this.sharedata.original_text,
            }).then(function(response) {
                if(response.status==200){
                    alert(response.data.msg);
                }
                if(response.status==201){
                    alert('提交成功！')
                }
                vm.sharedata.correctFeedbackDialogVisible = false;
                vm.sharedata.popupMenuShown = false;
                window.getSelection().removeAllRanges();
            });
        },
        handleCancel: function () {
            this.sharedata.correctFeedbackDialogVisible = false;
            this.sharedata.popupMenuShown = false;
            this.error = null;
            window.getSelection().removeAllRanges();
        }
    }
});

