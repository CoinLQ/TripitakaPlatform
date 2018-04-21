// 经文显示单元
Vue.component('lqtripitaka-sutra-unit', {
    props: ['data', 'sharedata'],
    template: `
    <span v-if="data.diffsegresult_id == undefined" v-html="data.text"></span>
    <span v-else-if="data.text.length == 0"><a href="#" class="lqtripitaka-diffseg" :diffsegresult_id="data.diffsegresult_id" @click="clickDiffSegResult()"><span class="diffseg-tag-white"></span></a></span>
    <span v-else><a href="#" class="lqtripitaka-diffseg" :diffsegresult_id="data.diffsegresult_id" @click="clickDiffSegResult()" v-html="data.text"></a></span>
    `,
    methods: {
        clickDiffSegResult: function () {
            this.sharedata.diffsegresult_id = this.data.diffsegresult_id;
            this.sharedata.judgeResultDialogVisible = true;
        }
    }
})

Vue.component('judge-result-dialog', {
    props: ['sharedata'],
    template: `
    <el-dialog title="判取" :visible.sync="sharedata.judgeResultDialogVisible" width="30%" @open="handleOpen" :before-close="handleCancel">
        <table class="table table-bordered">
            <thead>
            <tr><th>判取</th><th>版本</th><th>用字</th></tr>
            </thead>
            <tbody>
            <tr v-for="(diffsegtexts, text) in text_to_diffsegtexts">
                <td>
                    <input type="radio" :value="text" disabled="disabled" v-model="diffsegresult.selected_text" />
                </td>
                <td>{{ joinTnames(diffsegtexts) }}</td>
                <td>{{ text }}</td>
            </tr>
            </tbody>
        </table>
        <div class="row">
            <div class="col-md-3">反馈判取：</div>
            <div class="col-md-3">
                <select class="form-control" v-model="fb_text">
                    <option disabled value="">请选择文本</option>
                    <option v-for="(diffsegtexts, text) in text_to_diffsegtexts" :value="text">
                    {{ text }}
                    </option>
                </select>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <div>反馈说明：</div>
                <textarea class="form-control" rows="3" v-model="fb_comment"></textarea>
                <span slot="footer" class="dialog-footer">
                    <span class="alert alert-danger" v-if="error">{{ error }}</span>
                    <el-button type="primary" @click="handleOK">确定</el-button>
                    <el-button @click="handleCancel">取消</el-button>
                </span>
            </div>
        </div>
    </el-dialog>
    `,
    data: function () {
        return {
            diffsegresult: null,
            fb_text: null,
            fb_comment: '',
            text_to_diffsegtexts: {},
            error: null
        }
    },
    methods: {
        handleOpen: function () {
            this.fb_text = null;
            this.fb_comment = '';
            this.error = null;
            var url = 'http://api.lqdzj.cn/api/judge/' + this.sharedata.task_id
                + '/diffsegresults/' + this.sharedata.diffsegresult_id + '/';
            var vm = this;
            axios.get(url).then(function (response) {
                vm.diffsegresult = response.data;
                vm.text_to_diffsegtexts = {};
                var text_to_diffsegtexts = vm.text_to_diffsegtexts;
                var diffsegtexts = vm.diffsegresult.diffseg.diffsegtexts;
                for (var j = 0; j < diffsegtexts.length; ++j) {
                    var text = diffsegtexts[j].text;
                    if (text == null) {
                        continue;
                    }
                    if (text in text_to_diffsegtexts) {
                        text_to_diffsegtexts[text].push(diffsegtexts[j]);
                    } else {
                        text_to_diffsegtexts[text] = [diffsegtexts[j]];
                    }
                }
            });
        },
        handleOK: function () {
            if (this.fb_text == this.diffsegresult.selected_text) {
                alert('选择结果与原结果相同，不需要提交反馈。');
                return ;
            }
            axios.post('/api/judgefeedback/', {
                'fb_text': this.fb_text,
                'fb_comment': this.fb_comment,
                'diffsegresult': this.diffsegresult.id,
                'processor': 1
            }).then(function(response) {
                alert('提交成功！');
            });
        },
        handleCancel: function () {
            this.sharedata.judgeResultDialogVisible = false;
            this.error = null;
        },
        joinTnames: function (diffsegtexts) {
            var tnames = [];
            diffsegtexts.forEach(function (diffsegtext) {
                tnames.push(diffsegtext.tripitaka.shortname);
            });
            return tnames.join(' / ');
        }
    }
})

Vue.component('judge-fb-sutra-unit', {
    props: ['data', 'sharedata'],
    template: `
    <span v-if="data.diffsegresult_id == undefined" v-html="data.text"></span>
    <span v-else-if="data.text.length == 0"><a href="#" class="judge-fb-diffseg" :diffsegresult_id="data.diffsegresult_id"><span class="diffseg-tag-white"></span></a></span>
    <span v-else><a href="#" class="judge-fb-diffseg" :diffsegresult_id="data.diffsegresult_id" v-html="data.text"></a></span>
    `,
    methods: {
    }
})

Vue.component('judge-fb-show', {
    props: ['textdiffsegtexts', 'judgefeedback'],
    template: `
    <div>
        <table class="table table-bordered">
            <thead>
            <tr><th>版本</th><th>用字</th></tr>
            </thead>
            <tbody>
            <tr v-for="(diffsegtexts, text) in textdiffsegtexts">
                <td>{{ joinTnames(diffsegtexts) }}</td>
                <td>{{ text }}</td>
            </tr>
            </tbody>
        </table>
        <div v-if="judgefeedback">
            <div>原始判取：{{ judgefeedback.original_text }}</div>
            <div>反馈判取：{{ judgefeedback.fb_text }}</div>
            <div>反馈说明：</div>
            <div>{{ judgefeedback.fb_comment }}</div>
        </div>
    </div>
    `,
    methods: {
        joinTnames: function (diffsegtexts) {
            var tnames = [];
            diffsegtexts.forEach(function (diffsegtext) {
                tnames.push(diffsegtext.tripitaka.shortname);
            });
            return tnames.join(' / ');
        }
    }
})