var charListContainer = {
    char: '',
    page_size: 50,
    page_number: 1,
    filter: '-10', //show all
    order: '-accuracy',
    accuracy_base: NaN,
    accuracy_scope: 10,
    l_value: 0,
    r_value: 0.99,
    data: [],
    total: 0,
    timers: [],
    pagination: {},
    init: function() {
        charListContainer.initPageSize();
        charListContainer.initPagination();
        charListContainer.extras();
        charListContainer.char = $("#checkchar").text();
        charListContainer.page_number = 1;
        charListContainer.fetchDataAndRender();
    },
    initPageSize: function() {
        var page_size = $.cookie('charindex_page_size');
        if (page_size == undefined) {
            page_size = 50;
        }
        charListContainer.page_size = page_size;
    },
    initTable: function() {
    },
    initPagination: function() {
        $('.pagitor').click(function() {
            if ($(this).hasClass('first')) {
                page_number = 1;
            } else if ($(this).hasClass('previous')) {
                page_number = charListContainer.pagination.previous_page;
            } else if ($(this).hasClass('next')) {
                page_number = charListContainer.pagination.next_page;
            } else if ($(this).hasClass('last')) {
                page_number = charListContainer.pagination.total_pages;
            }else {
                return;
            }
            charListContainer.page_number = page_number;
            charListContainer.fetchDataAndRender();
        });
    },
    extras: function() {
        $('.accuracy_input').on('input', function(e) {
            charListContainer.accuracy_base = parseFloat($(this).val());
            charListContainer.switchAndRender();
        });
        var page_size = charListContainer.page_size;
        $("#LineControler button span:first-of-type").text(page_size);
        $('.accuracy_input').val('');

        $("#LineControler li a").click(function() {
            var page_size = $(this).text();
            charListContainer.page_size = page_size;
            $("#LineControler button span:first-of-type").text(page_size);
            $.cookie('charindex_page_size', page_size, { expires: 30 });
            charListContainer.page_number = 1;
            charListContainer.fetchDataAndRender();
        })

        $("#find_scope .dropdown-menu a").click(function() {
            var li = $(this);
            li.parent().parent().parent().find("button span:first-of-type").text(li.text());
            charListContainer.filter = li.data('value');
            charListContainer.switchAndRender();
        })

        $("#order_scope .dropdown-menu a").click(function() {
            var li = $(this);
            li.parent().parent().parent().find("button span:first-of-type").text(li.text());
            charListContainer.order = li.data('value');
            charListContainer.switchAndRender();
        })


        $("#accuracy_scope .dropdown-menu a").click(function() {
            var li = $(this);
            li.parent().parent().parent().find("button span:first-of-type").text(li.text());
            charListContainer.accuracy_scope = li.data('value');

            charListContainer.switchAndRender();
        })

        $("img.lazy").lazyload({
            effect: "fadeIn"
        });

        $('input.pagitor_input').keypress(function(event) {
            if (event.which == 13) {
                var page_number = parseInt($('.pagitor_input').val()) || 1;
                charListContainer.page_number = page_number;
                charListContainer.fetchDataAndRender();
            }
        });
    },
    handlerAction: function(is_correct, btn) {
        var arr = [];
        var clean_arr = []
        var charlist = $("#charListArea .char-image");
        for (var i = 0; i < charlist.length; i++) {
            var tmp = charlist[i];
            if (tmp.id === "") {
                continue; }
            if (!($(tmp).hasClass('error-char') || $(tmp).hasClass('correct-char'))) {
                arr.push(tmp.id);
            }
            clean_arr.push(tmp.id);
        }
        if (is_correct === 0) {
            arr = clean_arr;
        } else {
            $(".char-image").removeClass("twinkling");
        }
        var data = {};
        var updateNum = arr.length;
        var e_num = $("#charListArea .error-char").length;
        var c_num = $("#charListArea .correct-char").length;
        data.char = charListContainer.char;


    },
    paginationRender: function() {
        var total_pages = this.pagination.total_pages;
        $('.pagitor_input').val(this.page_number);
        $('.pagitor_input').attr('max', total_pages);
        $('.total_page').text('/ ' + total_pages);
    },
    startWaitingAnimate: function(char, least) {
        var t = new TimeLeft(char, least);
        this.timers = this.timers.filter(function(el) {
            return el.char != char;
        });
        this.timers.push(t);
        t.Start();
    },
    recallWaitingAnimate: function() {
        var that = this;
        t = this.timers.filter(function(el) {
            return el.char == that.char && el.Enable == true;
        });
        if (t[0]) t[0].showCircle();
    },
    hideWaitingAnimate: function() {
        var that = this;
        t = this.timers.filter(function(el) {
            return el.char == that.char;
        });
        if (t[0]) t[0].hideCircle();
    },
    checkDict: function() {
        url = "http://hanzi.lqdzj.cn/variant_detail?q="
        url += charListContainer.char;
        var _open = window.open(url);
        if (_open == null || typeof(_open) == 'undefined')
            console.log("Turn off your pop-up blocker!");
    },
    switchAndRender: function() {
        return this.fetchDataAndRender();
    },
    fetchDataAndRender: function() {
        var that = this;
        if (this.char == '') {
            return;
        }
        var query = "http://www.dzj3000.com/api/characterread?page_size=" + this.page_size + "&char=" + this.char + "&page=" + this.page_number + "&ordering=" + this.order;
        var accuracy_cap, accuracy_floor;
        if (this.accuracy_base) {
            accuracy_cap = parseInt(this.accuracy_base * 1000 + this.accuracy_scope);
            accuracy_floor = parseInt(this.accuracy_base * 1000 - this.accuracy_scope);

            if (accuracy_cap < 1 || this.accuracy_scope == 0) {
                query += "&accuracy__lte=" + accuracy_cap;
            }
            if (accuracy_floor > -1 || this.accuracy_scope == 0) {
                query += "&accuracy__gte=" + accuracy_floor;
            }

        }
        if (this.filter != -10) {
            query += "&is_correct=" + this.filter;
        }

        $.getJSON(query, function(result) {
            that.data = result.models;
            new_models = _.map(result.models, function(item) {
                var class_name;
                if (item.is_correct == 1) {
                    cls_name = 'o-correct-char'
                } else if (item.is_correct == -1) {
                    cls_name = 'o-error-char'
                } else {
                    cls_name = ''
                }
                item['cls_name'] = cls_name;
                item.accuracy = item.accuracy * 1.0 / 1000
                return item;
            });

            char_list.items = new_models;
            that.pagination = result.pagination;
            that.paginationRender();
        });
    }
}

