
Vue.component('doubt-list', {
    props: ['doubts'],
    template: `
        <el-table
        :data="doubts"
        style="width: 100%"
        max-height="250">
        <el-table-column
          fixed
          prop="id"
          label="ID"
          width="150">
        </el-table-column>
        <el-table-column
          prop="doubt_text"
          label="存疑文本"
          width="120">
        </el-table-column>
        <el-table-column
          prop="doubt_comment"
          label="存疑理由"
          width="120">
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作"
          width="120">
          <template slot-scope="scope">
            <el-button
              @click.native.prevent="deleteRow(scope.$index, doubts)"
              type="text"
              size="small">
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    `,
    data: function() {
        return {
            doubts: [],
            current_doubt: {},
        }
    },
    methods: {
        deleteRow: function(index, rows) {
            rows.splice(index, 1);
        }
    }
})