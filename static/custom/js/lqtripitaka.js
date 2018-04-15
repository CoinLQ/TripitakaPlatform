function lqtripitaka_merge_text_punct(text, diffsegresult_pos_lst, punct_lst) {
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
        if (diffsegresult_pos_lst[diffseg_idx] == undefined) {
            console.log('hello')
        }
        if (diffseg_idx < diffsegresult_pos_lst.length) {
            if (pos > diffsegresult_pos_lst[diffseg_idx].position) {
                pos = diffsegresult_pos_lst[diffseg_idx].position;
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
            console.log(obj)
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
                console.log(obj)
                result.push(obj);
            }
            obj = null;
            diffseg_endpos = text.length + 1;
        }

        // 处理标点
        while (punct_idx < punct_lst.length) {
            if (punct_lst[punct_idx][0] <= i) {
                var punct_ch = punct_lst[punct_idx][1];
                if (punct_ch == '\n') {
                    if (obj != null) {
                        if (obj['type'] == TEXT) {
                            obj['text'] = obj['text'].join('');
                            console.log(obj)
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

        if (diffseg_idx < diffsegresult_pos_lst.length) {
            var pos = diffsegresult_pos_lst[diffseg_idx].position;
            if (pos == i) {
                diffseg_endpos = pos + diffsegresult_pos_lst[diffseg_idx].selected_length;
                if (obj != null) {
                    if (obj['type'] == TEXT || obj['type'] == SEG_TEXT) {
                        obj['text'] = obj['text'].join('');
                    } else if (obj['type'] == SEG_LINES) {
                        obj['lines'].push(obj['text'].join(''));
                        obj['text'] = [];
                    }
                    console.log(obj)
                    result.push(obj);
                    obj = null;
                }
                if (pos == diffseg_endpos) {
                    obj = {
                        'diffsegresult_id': diffsegresult_pos_lst[diffseg_idx].diffsegresult_id,
                        'type': SEG_NOTEXT
                    };
                    console.log(obj)
                    result.push(obj);
                    obj = null;
                    diffseg_endpos = text.length + 1;
                } else {
                    obj = {
                        'diffsegresult_id': diffsegresult_pos_lst[diffseg_idx].diffsegresult_id,
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

// 经文显示单元
Vue.component('lqtripitaka-sutra-unit', {
    props: ['data', 'sharedata'],
    template: `
    <span>
        <span v-if="data.type == 0">{{ data.text }}</span>
        <span v-else-if="data.type == 1" tag="br"><br /></span>
        <span v-else-if="data.type == 2"><a href="#" :diffsegresult_id="data.diffsegresult_id" :class="className" @click="choiceThis()"><span class="diffseg-tag-white"></span></a></span>
        <span v-else-if="data.type == 3"><a href="#" :diffsegresult_id="data.diffsegresult_id" :class="className" @click="choiceThis()">{{ data.text }}</a></span>
        <span v-else>
            <a href="#" :diffsegresult_id="data.diffsegresult_id" :class="className" @click="choiceThis()">
                <span v-for="(line, index) in data.lines" tag="seg">{{ line }}<br v-if="index < data.lines.length-1" /></span>
            </a>
        </span>
    </span>
    `,
    computed: {
        className: function() {
            if (this.data.type == 2) {
                if (this.sharedata.diffsegresult_id == this.data.diffsegresult_id) {
                    return 'diffseg-tag-notext-selected';
                } else {
                    let elem = _.find(this.sharedata.diffsegresults, function(v) {return v.id == this.data.diffseg_id}.bind(this))
                    if (elem && elem.selected_text) {
                        return 'diffseg-tag-judged';
                    } else {
                        return 'diffseg-tag-notext';
                    }
                }
            } else if (this.data.type == 3) {
                if (this.sharedata.diffsegresult_id == this.data.diffsegresult_id) {
                    return 'diffseg-tag-selected';
                }else {
                    let elem = _.find(this.sharedata.diffsegresults, function(v) {return v.id == this.data.diffseg_id}.bind(this))
                    if (elem && elem.selected_text) {
                        return 'diffseg-tag-judged';
                    } 
                }
            }
            return '';
        }
    },
    methods: {
        choiceThis: function() {
        }
    }
})