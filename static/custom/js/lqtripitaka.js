// 经文显示单元
Vue.component('lqtripitaka-sutra-unit', {
    props: ['data', 'sharedata'],
    template: `
    <span v-if="data.diffsegresult_id == undefined" :position="data.position" v-html="data.text"></span>
    <span v-else-if="data.text.length == 0" :position="data.position"><a href="#" class="lqtripitaka-diffseg" :diffsegresult_id="data.diffsegresult_id" @click="clickDiffSegResult()"><span class="lqtripitaka-diffseg-tag-white"></span></a></span>
    <span v-else :position="data.position"><a href="#" class="lqtripitaka-diffseg" :diffsegresult_id="data.diffsegresult_id" @click="clickDiffSegResult()" v-html="data.text"></a></span>
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
            <div class="col-md-4">反馈判取：</div>
            <div class="col-md-4">
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
            var url = '/api/judge/' + this.sharedata.task_id
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
            var vm = this;
            axios.post('/api/judgefeedback/', {
                'fb_text': this.fb_text,
                'fb_comment': this.fb_comment,
                'diffsegresult': this.diffsegresult.id,
                'processor': 1
            }).then(function(response) {
                alert('提交成功！');
                vm.sharedata.judgeResultDialogVisible = false;
                vm.error = null;
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
            <div>审查意见：{{ getResponseDesc(judgefeedback.response) }}</div>
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
        },
        getResponseDesc: function(response) {
            if (response == 1) {
                return '未处理';
            } else if (response == 2) {
                return '同意';
            } else if (response == 3) {
                return '不同意';
            }
        }
    }
})

function punct_merge_text_punct(text, puncts, punct_result) {
    //clean_linefeed(puncts);
    var TYPE_TEXT = 1;
    var TYPE_SEP = 2;
    var TYPE_BR = 3;

    var result_idx = 0;
    var result_len = punct_result.length;

    var punctseg_lst = [];
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

Vue.component('punct-feedback-dialog', {
    props: ['sharedata'],
    template: `
    <el-dialog title="标点反馈" :visible.sync="sharedata.punctFeedbackDialogVisible" width="50%" @open="handleOpen" :before-close="handleCancel">
        <div class="row">
            <div class="punct-feedback-region">
                <span v-for="punctseg in sharedata.punctseg_lst">
                    <span is="punct-show-seg" :punctseg="punctseg" :sharedata="sharedata"></span>
                </span>
            </div>
        </div>
        <div class="row">
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
            error: null
        }
    },
    methods: {
        handleOpen: function () {
        },
        handleOK: function () {
            var punct_result = [];
            this.sharedata.punctseg_lst.forEach(function(punctseg) {
                punctseg.user_puncts.forEach(function(punct_unit) {
                    punct_result.push([punct_unit[0], punct_unit[1]]);
                });
            });
            var vm = this;
            axios.post('/api/lqpunctfeedback/', {
                'lqpunct': this.sharedata.lqpunct_id,
                'start': this.sharedata.selection_start,
                'end': this.sharedata.selection_end,
                'fb_punctuation': JSON.stringify(punct_result)
            }).then(function(response) {
                alert('提交成功！');
                vm.sharedata.punctFeedbackDialogVisible = false;
            });
        },
        handleCancel: function () {
            this.sharedata.punctFeedbackDialogVisible = false;
            this.error = null;
        }
    }
})

// (龙泉)经文显示单元
Vue.component('lqtripitaka-sutra-view', {
    props: ['data', 'sharedata'],
    template: `
    <span v-if="data.diffsegresult_id == undefined" :position="data.position" ><span v-for="text in normal_text"><span v-if="text.type == 'p'"  v-html="text.value"></span><span v-else-if="text.type == 't'" v-html="text.value"></span></span></span>
    <span v-else-if="data.text.length == 0" :position="data.position"><a href="#" class="lqtripitaka-diffseg" :diffsegresult_id="data.diffsegresult_id" @click="clickDiffSegResult()"><span class="lqtripitaka-diffseg-tag-white"></span></a></span>
    <span v-else :position="data.position"><a href="#" class="lqtripitaka-diffseg" :diffsegresult_id="data.diffsegresult_id" @click="clickDiffSegResult()" v-html="data.text"></a></span>
    `,
    data: function () {
        return {
            normal_text:[],
        }
    },
    created: function(){
        let vm = this;
		
        this.$nextTick(function(){
            vm.normal_text = vm.getNomalText();
        })
    },
    methods: {
        clickDiffSegResult: function () {
            this.sharedata.diffsegresult_id = this.data.diffsegresult_id;
            this.sharedata.judgeResultDialogVisible = true;
        },
        getNomalText: function () {
            var normal_text = this.data.text.split("<br />");
            var text_arr = []
            if (normal_text.length <= 1) {
                text_arr[0] = {type:'t',value:normal_text[0]}
            }else{
                for (var i = 0; i<normal_text.length; i++) {
                    if (i == 0) {
                        text_arr[i] = {type:'t',value:normal_text[i]}
                    }else{
                        text_arr[i] = {type:'p',value:"<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + normal_text[i]}
                        
                    }
                }
            }
            return text_arr;
            
        }
    }
})

Vue.component('judge-result-view', {
    props: ['sharedata'],
    template: `
    <el-dialog title="校勘记" :visible.sync="sharedata.judgeResultDialogVisible" width="30%" @open="handleOpen" :before-close="handleCancel">
        <table class="table table-bordered">
            <thead>
            <tr><th>选定</th><th>版本</th><th>用字</th></tr>
            </thead>
            <tbody>
            <tr v-for="(diffsegtexts, text) in text_to_diffsegtexts">
                <td>
                    <li v-if="text == diffsegresult.selected_text">&radic;</li>
                </td>
                <td>{{ joinTnames(diffsegtexts) }}</td>
                <td>{{ text }}</td>
            </tr>
            </tbody>
        </table>
        <el-button type="danger" @click="showFeedBack=!showFeedBack">反馈</el-button>
        <div v-if="showFeedBack">
            <div class="row" >
                <span><br/></span>
                <div class="col-md-4">反馈判取：</div>
                <div class="col-md-4">
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
                        <span><br/></span>
                        <el-button type="primary" @click="handleOK">确定</el-button>
                        <el-button @click="handleCancel">取消</el-button>
                    </span>
                </div>
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
            error: null,
            showFeedBack: false,
        }
    },
    methods: {
        handleOpen: function () {
            this.fb_text = null;
            this.fb_comment = '';
            this.error = null;
            var url = '/api/judge/' + this.sharedata.task_id
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
            var vm = this;
            axios.post('/api/judgefeedback/', {
                'fb_text': this.fb_text,
                'fb_comment': this.fb_comment,
                'diffsegresult': this.diffsegresult.id,
                'processor': 1
            }).then(function(response) {
                alert('提交成功！');
                vm.sharedata.judgeResultDialogVisible = false;
                vm.error = null;
                this.showFeedBack = false;
            }).catch(function (error) {
                console.log(error.data.fb_comment);
                if ("该字段不能为空。" == error.data.fb_comment) {
                    alert('“反馈说明”不能为空。');
                }else{
                    alert('反馈失败！');
                }
                
            });
        },
        handleCancel: function () {
            this.sharedata.judgeResultDialogVisible = false;
            this.showFeedBack = false;
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

Vue.component('net-read-dialog', {
    name: 'net-read-dialog',
    props: ['result','sutraname','author'],
    template: `
    <div id = "content"  style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgb(181,229,181) ; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
        <div id="netread"  style=" width: 50%;height: 100%; padding: 10px ;border-radius: 0px;border-width: 1px;border-color: lightgray; background:white;text-align:left; overflow: scroll;">
            <span v-if="sutraname != ''" text-align="center" style="display:block; text-align:center; -webkit-text-fill-color: red; font-size: 24;">{{ sutraname }}</span>
            <span v-if="author != ''"  style="display:block; text-align:center; -webkit-text-fill-color: gray; font-size: 16;">{{ author }}</span>
            <span style="font-size:24px; " v-html="merged_text"></span>
        </div>
    </div>
    `,
    data: function () {
        return {
			merged_text:'',
        }
	},
    created: function() {
        let vm = this;
		
        this.$nextTick(function(){
            vm.merged_text = vm.merged();
        })
    },
    methods: {
        merged: function(){
            var text = '';
            for ( var e in this.result) {
                text = text + this.result[e].text;
            }
            var re = new RegExp("<br />", "g");// 匹配所有的<br />，g表示全部global
            text = text.replace(re,"<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;")
            return text;
        },
    }
})

Vue.component('focus-read-dialog', {
    name: 'focus-read-dialog',
    props: ['result','sutraname','author'],
    template: `
    <div id = "content" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgb(181,229,181) ; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
        <div id="netread"  style=" width: 60%;height: 80%; padding: 10px ;border-radius: 0px;border-width: 1px;border-color: lightgray; background:white;text-align:left; overflow: scroll; background: rgb(199,237,204); ">
            <span v-if="sutraname != ''" text-align="center" style="display:block; text-align:center; -webkit-text-fill-color: red; font-size: 24;">{{ sutraname }}</span>
            <span v-if="author != ''"  style="display:block; text-align:center; -webkit-text-fill-color: gray; font-size: 16;">{{ author }}</span>
            <span style="font-size:24px;" v-html="merged_text"></span>
        </div>
    </div>
    `,
    data: function () {
        return {
			merged_text:'',
        }
	},
    created: function() {
        let vm = this;
		
        this.$nextTick(function(){
            vm.merged_text = vm.merged();
        })
    },
    methods: {
        merged: function(){
            var text = '';
            for ( var e in this.result) {
                text = text + this.result[e].text;
            }
            var re = new RegExp("<br />", "g");// 匹配所有的<br />，g表示全部global
            text = text.replace(re,"<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;")
            return text;
        }
    }
})

Vue.component('turn-page-dialog', {
    name: 'turn-page-dialog',
    props: ['text'],
    template: `
    <div id="book">
        <div><span v-html="page4"></span></div>
        <div>{{page3}}</div>
        <div>{{page2}}</div>
		<div>{{page1}}</div>
	</div>
	`,
	data: function () {
        return {
			page_lst:[],
			page1:"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
			page2:"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
			page3:"cccccccccccccccccccccccccccccccccccccccccccccccc",
            page4:"ddddddddddddddddddddddddddddddddddddddddddddddddddd",
            pageNumber:1,
        }
	},
	created: function() {
        let vm = this;
		vm.reloadText();
		this.$nextTick(function(){
        
			var book = document.getElementById("book");
			var pages = book.getElementsByTagName("div");
			var pageNumber = 1;
            var rota = -180;
            console.log("create");
			book.onclick = function () {
                
				book.style.left = "65%";
				// pages[pageNumber].style.transform = "rotateY(" + rota + "deg)";
				// pageNumber--;
                // rota += 10;
                
                var roundFlag = Math.ceil(pageNumber/4);
               
                console.log("roundFlag:"+roundFlag);
                if (pageNumber == 1) {
                    pages[3].style.transform = "rotateY(" + rota*roundFlag + "deg)";//当前页
                }else if (pageNumber == 2) {
                    pages[3].style.transform = "rotateY(" + (rota*roundFlag-0.1) + "deg)";//前一页
                    pages[2].style.transform = "rotateY(" + rota*roundFlag + "deg)";//当前页
                }else if (pageNumber == 3) {
                    pages[3].style.transform = "rotateY(" + (rota*(roundFlag+1)+0.1) + "deg)";//前二页
                    pages[2].style.transform = "rotateY(" + (rota*roundFlag-0.1) + "deg)";//前一页
                    pages[1].style.transform = "rotateY(" + (rota*roundFlag) + "deg)";//当前页
                }else if (pageNumber == 4) {
                    //roundFlag == 1
                    pages[3].style.transform = "rotateY(" + rota*(roundFlag+1) + "deg)";//前三页
                    pages[2].style.transform = "rotateY(" + (rota*(roundFlag+1)+0.1) + "deg)";//前二页
                    pages[1].style.transform = "rotateY(" + (rota*roundFlag-0.1) + "deg)";//前一页
                    pages[0].style.transform = "rotateY(" + (rota*roundFlag) + "deg)";//当前页
                }else if (pageNumber > 4) {
                    //roundFlag == 2
                    var currentPageFlag = 4 - (pageNumber+1) % 4 - 1;//pages[currentPageFlag]的参数
                    
                    var page3Flag = rota*([pageNumber/2]);
                    var page2Flag = rota*([(pageNumber-1)/2]);
                    var page1Flag = rota*([(pageNumber-2)/2]);
                    var page0Flag = rota*([(pageNumber-3)/2]);
                    var pageThinDeg1 =-89.9;
                    var pageThinDeg2 =0;
                    console.log("pageNumber:"+pageNumber+"--currentPageFlag:"+currentPageFlag);
        
                    if (currentPageFlag == 0) {
                        pages[3].style.transform = "rotateY(" + (page3Flag+pageThinDeg2) + "deg)";//前三页
                        pages[2].style.transform = "rotateY(" + (page2Flag+pageThinDeg1) + "deg)";//前二页
                        pages[1].style.transform = "rotateY(" + (page1Flag) + "deg)";//前一页
                        pages[0].style.transform = "rotateY(" + (page0Flag) + "deg)";//当前页
                    }else if (currentPageFlag == 1) {
                        pages[0].style.transform = "rotateY(" + (page0Flag+pageThinDeg2) + "deg)";//前三页
                        pages[3].style.transform = "rotateY(" + (page3Flag+pageThinDeg1) + "deg)";//前二页
                        pages[2].style.transform = "rotateY(" + (page2Flag) + "deg)";//前一页
                        pages[1].style.transform = "rotateY(" + (page1Flag) + "deg)";//当前页
                    }else if (currentPageFlag == 2) {
                        pages[1].style.transform = "rotateY(" + (page1Flag) + "deg)";//前三页
                        pages[0].style.transform = "rotateY(" + (page0Flag+pageThinDeg1) + "deg)";//前二页
                        pages[3].style.transform = "rotateY(" + (page3Flag+pageThinDeg2) + "deg)";//前一页
                        pages[2].style.transform = "rotateY(" + (page2Flag) + "deg)";//当前页
                    }else if (currentPageFlag == 3) {
                        pages[2].style.transform = "rotateY(" + (page2Flag+pageThinDeg2) + "deg)";//前三页
                        pages[1].style.transform = "rotateY(" + (page1Flag+pageThinDeg1) + "deg)";//前二页
                        pages[0].style.transform = "rotateY(" + (page0Flag) + "deg)";//前一页
                        pages[3].style.transform = "rotateY(" + (page3Flag) + "deg)";//当前页
                    }
                }

                
                pageNumber++;
                vm.pageNumber = pageNumber;
				// if (pageNumber < 0) {
				// 	for (var i = 0; i < pages.length; i++) {
				// 		pages[i].style.transform = "rotateY(0deg)";
				// 	}
				// 	book.style.left = "50%";
				// 	pageNumber = 3;
				// 	rota = -180;
				// }
			}
		})
    },
    watch: {
        text: function(val,oldVal){
            if (oldVal != val) {
                let vm = this;
                vm.pageNumber =1;
                vm.reloadText();
                this.$nextTick(function(){
                    var book = document.getElementById("book");
                    var pages = book.getElementsByTagName("div");
                    pages[3].style.transform = "rotateY(" + 0 + "deg)";
                    pages[2].style.transform = "rotateY(" + 0 + "deg)";
                    pages[1].style.transform = "rotateY(" + 0 + "deg)";
                    pages[0].style.transform = "rotateY(" + 0 + "deg)";
                })
            }
        },
        pageNumber: function(val,oldVal){
            
            if (oldVal != val) {
                var index = 4*(Math.ceil((val+1)/4)-1);
                console.log("index:"+index);
                val++;
                if ((val-2)%4 == 0){//page1 reload
                    this.page1 = this.page_lst[this.pageNumber-1]+this.pageNumber;
                }else if ((val-3)%4 == 0){
                    this.page2 = this.page_lst[this.pageNumber-1]+this.pageNumber;
                }else if ((val-4)%4 == 0){
                    this.page3 = this.page_lst[this.pageNumber-1]+this.pageNumber;
                }else if ((val-5)%4 == 0){
                    this.page4 = this.page_lst[this.pageNumber-1]+this.pageNumber;
                }
            }
            
        }
    },
    methods: {
		reloadText: function () {
            
            this.page_lst = this.text.split("\n");
            this.page1 = this.page_lst[0];
            this.page2 = this.page_lst[1];
            this.page3 = this.page_lst[2];
            this.page4 = this.page_lst[3];
        },
	}
      
})

Vue.component('three-dimensions-dialog', {
    name: 'three-dimensions-dialog',
    props: ['result','sutraname','author'],
    template: `
    <div id = "content" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgb(181,229,181) ; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
        <div id="box" style="overflow: scroll; width: 61.8%;">
            <p id="flashlight"> 
                <span id="flash" v-if="sutraname != ''" text-align="center" style="display:block; text-align:center; -webkit-text-fill-color: red;">{{ sutraname }}</span>
                <span id="flash" v-if="author != ''"  style="display:block; text-align:center; -webkit-text-fill-color: gray; font-size: 20;">{{ author }}</span>
                <span id="flash" style="-webkit-text-fill-color: yellow;" v-html="merged_text"></span> 
            </p>
        </div>
    </div>
    `,
    data: function () {
        return {
			merged_text:'',
        }
	},
    created: function() {
        let vm = this;
		
        this.$nextTick(function(){
            vm.merged_text = vm.merged();
        })
    },
    methods: {
        merged: function(){
            var text = '';
            for ( var e in this.result) {
                text = text + this.result[e].text;
            }
            var re = new RegExp("<br />", "g");// 匹配所有的<br />，g表示全部global
            text = text.replace(re,"<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;")
            return text;
        }
    }
})
