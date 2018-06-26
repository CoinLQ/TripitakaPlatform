
Vue.component('doubt-list', {
  props: ['doubts', 'task_id', 'current_doubt', 'task_typ'],
  template: `
<table class="doubt-table">
<thead>
  <th>行数</th>
  <th>存疑文本</th>
  <th>存疑理由</th>
  <th>操作</th>
</thead>
<tbody>
  <tr v-for="(item, index) in doubts" @click="handleCurrentChange(item)" v-show="!item.processed">
    <td>{{item.id}}</td>
    <td>{{item.doubt_text}}</td>
    <td>{{item.doubt_comment}}</td>
    <td><em v-if="task_typ!=2" @click="deleteRow(index, doubts)">移除</em>
    <em v-else v-show="!item.processed" @click="processRow(index, doubts)">完成处理</em></td>
  </tr>
</tbody>
</table>
`,
  data() {
    return {}
  },
  methods: {
    handleCurrentChange(val) {
      this.$emit('update:current_doubt', val);
    },
    deleteRow(index, rows) {
      axios.delete('/api/doubt_seg/' + this.task_id + '/' + rows[index].id + '/delete/').then(function (response) {
        this.$delete(this.doubts, index)
        this.$emit('update:doubts', this.doubts);
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });


    },
    processRow(index, rows) {
      rows[index].processed = true;
      axios.put('/api/doubt_seg/' + this.task_id + '/' + rows[index].id + '/', {
        task: this.task_id,
        processed: true
      }).then(function (response) {
        this.$emit('update:doubts', this.doubts);
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });
    },
    loadDoubtSeg(){
      axios.get('/api/doubt_seg/' + this.task_id + '/list/?task=' + this.task_id).then(function (response) {
        this.$emit('update:doubts', _.reverse(response.data.models))
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });
    }
  },
  mounted() {
    this.loadDoubtSeg();
  }
});



Vue.component('mark-list', {
  props: ['marks', 'task_id', 'current_mark'],
  template: `
        <el-table
        :data="marks"
        :cell-style="{height: '20px'}"
        highlight-current-row
        @current-change="handleCurrentChange"
        style="width: 100%"
        max-height="200">
        <el-table-column
          prop="start"
          label="标记起点"
          >
        </el-table-column>
        <el-table-column
          prop="end"
          label="标记终点"
          >
        </el-table-column>
        <el-table-column
          prop="mark_typ"
          label="标记类型"
          >
          <template slot-scope="scope">
            <span >{{ typeStr(scope.row.mark_typ) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作"
          width="120">
          <template slot-scope="scope">
            <el-button 
              @click.native.prevent="deleteRow(scope.$index, marks)"
              type="text"
              size="small">
              移除
            </el-button>

          </template>
        </el-table-column>
      </el-table>
    `,
  data() {
    return {}
  },
  methods: {
    handleCurrentChange(val) {
      this.$emit('update:current_mark', val);
    },
    typeStr(val) {
      switch (val) {
        case 1:  //标题
            return '标题';
        case 2: //作译者
            return '作译者';
        case 3: //序
            return '序';
        case 4: //千字文
            return '千字文';
        case 5: //跋
            return '跋';
        case 6: //行间小字
            return '行间小字';
        case 11: //偈颂
            return '偈颂';
        case 12: //夹注小字
            return '夹注小字';
        case 13: //梵文
            return '梵文';
        case 14: //咒语
            return '咒语';
      }
    },
    deleteRow(index, rows) {
      this.$delete(this.marks, index)
      this.$emit('update:marks', this.marks);
    },
    processRow(index, rows) {
      rows[index].processed = true;
      axios.put('/api/mark_seg/' + this.task_id + '/' + rows[index].id + '/', {
        task: this.task_id,
        processed: true
      }).then(function (response) {
        this.$emit('update:marks', this.marks);
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });
    },
    loadMarkSeg(){
      // axios.get('/api/mark_seg/' + this.task_id + '/list/?task=' + this.task_id).then(function (response) {
      //   this.$emit('update:marks', _.reverse(response.data.models))
      // }.bind(this))
      //     .catch(function (error) {
      //       console.log(error)
      //     });
    }
  },
  mounted() {
    this.loadMarkSeg();
  }
})


Vue.component('mark-doubt-list', {
  props: ['marks', 'task_id', 'current_mark', 'accept-this'],
  template: `
        <el-table
        :data="marks"
        :cell-style="{height: '20px'}"
        highlight-current-row
        @current-change="handleCurrentChange"
        style="width: 100%"
        max-height="200">
        <el-table-column
          prop="start"
          label="标记起点"
          >
        </el-table-column>
        <el-table-column
          prop="end"
          label="标记终点"
          >
        </el-table-column>
        <el-table-column
          prop="mark_typ"
          label="标记类型"
          width="100">
          <template slot-scope="scope">
            <span >{{ typeStr(scope.row.mark_typ) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作"
          width="120">
          <template slot-scope="scope">
            <el-button 
              @click.native.prevent="deleteRow(scope.$index, marks)"
              type="text"
              size="small">
              移除
            </el-button>
            <el-button 
              @click.native.prevent="processRow(scope.$index, marks)"
              type="text"
              size="small">
              接受
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    `,
  data() {
    return {}
  },
  methods: {
    handleCurrentChange(val) {
      this.$emit('update:current_mark', val);
    },
    typeStr(val) {
      switch (val) {
        case 1:  //标题
            return '标题';
        case 2: //作译者
            return '作译者';
        case 3: //序
            return '序';
        case 4: //千字文
            return '千字文';
        case 5: //跋
            return '跋';
        case 6: //行间小字
            return '行间小字';
        case 11: //偈颂
            return '偈颂';
        case 12: //夹注小字
            return '夹注小字';
        case 13: //梵文
            return '梵文';
        case 14: //咒语
            return '咒语';

      }
    },
    deleteRow(index, rows) {
      this.$delete(this.marks, index)
      this.$emit('update:marks', this.marks);
      this.$emit('update:current_mark', {});
    },
    processRow(index, rows) {
      rows[index].processed = true;
      this.$emit('accept', this.marks[index])
      this.deleteRow(index, rows)
    },
    loadMarkSeg(){
      // axios.get('/api/mark_seg/' + this.task_id + '/list/?task=' + this.task_id).then(function (response) {
      //   this.$emit('update:marks', _.reverse(response.data.models))
      // }.bind(this))
      //     .catch(function (error) {
      //       console.log(error)
      //     });
    }
  },
  mounted() {
    this.loadMarkSeg();
  }
});

Vue.component('correct-feedback-list', {
  props: ['cut_data', 'fb_id', 'processor'],
  template: `
        <el-table
        :data="cut_data"
        :cell-style="{height: '20px'}"
        highlight-current-row
        style="width: 100%"
        max-height="200">
        <el-table-column
          prop="origin_text"
          label="原始文本"
          width="150">
        </el-table-column>
        <el-table-column
          prop="fb_text"
          label="反馈文本"
          width="150">
        </el-table-column>
        <el-table-column
          prop="fb_comment"
          label="反馈意见"
          width="220">
        </el-table-column>
        <el-table-column v-if="processor"
          prop="processor"
          label="处理人"
          width="220">
        </el-table-column>
        <el-table-column v-if="processor==0 && !processed"
          fixed="right"
          label="操作"
          width="120"
          key="a">
          <template slot-scope="scope">
            <el-button
              @click="processfb(2)"
              type="text"
              size="media">
              同意
            </el-button>
            <el-button
              @click="processfb(3)"
              type="text"
              size="media">
              拒绝
            </el-button>
          </template>
        </el-table-column>
        
        <el-table-column v-else 
          prop="response"
          fixed="right" 
          label="处理意见" 
          width="120">
        </el-table-column>
      </el-table>
    `,
  data() {
    return { processed:false }
  },
  methods: {
    processfb(re_type) {
      axios.patch('/api/correctfeedback/' + this.fb_id + '/', {
        'response': re_type,
      }).then(function (response) {
        this.processed = true;
        this.$emit('update:cut_data', response.data);
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });
    },
  },
});
