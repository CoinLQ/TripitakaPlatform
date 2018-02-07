
+function ($) { "use strict";

// POPOVER PUBLIC CLASS DEFINITION
// ===============================

var BrowserPop = function (element, options) {
  this.einit('browserpop', element, options)
}

BrowserPop.DEFAULTS = $.extend({} , $.fn.popover.Constructor.DEFAULTS, {
  container: 'body'
, trigger: 'manual'
, placement: function(tip, el) {
  var $tip = $(tip)
  var $el = $(el)

  var tip_width = $tip.width(),
      tip_height = $tip.height(),
      el_width = $el.width(),
      el_height = $el.height(),
      client_width = document.body.clientWidth,
      gap = 20

  var top_gap = 100,
      left_gap = 80,
      right_gap = client_width - left_gap - el_width

  if(top_gap > tip_height + gap && left_gap > tip_width/2 + gap && right_gap > tip_width/2 + gap){
    return 'bottom'
  }
  return 'top'
}
, template: '<div class="popover browserpop browserable"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
})


// NOTE: POPOVER EXTENDS tooltip.js
// ================================

BrowserPop.prototype = $.extend({}, $.fn.popover.Constructor.prototype)

BrowserPop.prototype.constructor = BrowserPop

BrowserPop.prototype.einit = function (type, element, options) {
  this.init(type, element, options)
  this.content = null
  this.$element.on('click.' + this.type, $.proxy(this.beforeToggle, this))

  this.$text = this.$element.parent().parent().find('.browserable-field')
  this.field = this.$element.data('browserable-field')
}

BrowserPop.prototype.getDefaults = function () {
  return BrowserPop.DEFAULTS
}

BrowserPop.prototype.beforeToggle = function() {

  var $el = this.$element

    if(this.content == null){
      var that = this
      //$el.find('>i').removeClass('fa fa-edit').addClass('fa-spinner fa-spin')
      $.ajax({
        url: $el.data('browserable-loadurl'),
        success: function(content){
          //$el.find('>i').removeClass('fa-spinner fa-spin').addClass('fa fa-edit')
          that.content = content
          that.toggle()
        },
        dataType: 'html'
      })
    } else {
      this.toggle()
    }

}

BrowserPop.prototype.setContent = function () {
  var $tip    = this.tip()
  var title   = this.getTitle()

  $tip.find('.popover-title').html('<button class="close" data-dismiss="browserpop">&times;</button>' + title)
  $tip.find('.popover-content').html(this.content)

  var $form = $tip.find('.popover-content > form')
  $form.exform()
  $form.submit($.proxy(this.submit, this))

  this.$form = $form
  this.$mask = $('<div class="mask"><h2 style="text-align:center;"><i class="fa-spinner fa-spin fa fa-large"></i></h2></div>')
  $tip.find('.popover-content').prepend(this.$mask)

  $tip.removeClass('fade top bottom left right in')

  //bind events
  $tip.find('[data-dismiss=browserpop]').on('click.' + this.type, $.proxy(this.leave, this, this))

  var me = ((Math.random() * 10) + "").replace(/\D/g, '')
  var click_event_ns = "click." + me + " touchstart." + me
  var that = this

  // $('body').on(click_event_ns, function(e) {
  //   if ( !$tip.has(e.target).length ) { that.hide() }
  // })

  $(document).bind('keyup.browserpop', function(e) {
    if (e.keyCode == 27) { that.leave(that) }
    return
  })
}

BrowserPop.prototype.hasContent = function () {
  return this.getTitle() || this.content
}

BrowserPop.prototype.submit = function(e) {
    e.stopPropagation()
    e.preventDefault()

    $.when(this.save())
    .done($.proxy(function(data) {
      this.$mask.hide()
      this.$mask.parents('.popover').hide()
      if(data['result'] != 'success' && data['errors']){
        var err_html = []
        for (var i = data['errors'].length - 1; i >= 0; i--) {
          var e = data['errors'][i]
          for (var j = e['errors'].length - 1; j >= 0; j--) {
            err_html.push('<span class="help-block error">'+e['errors'][j]+'</span>')
          }
        }
        this.$form.find(".control-group").addClass('has-error')
        this.$form.find('.controls').append(err_html.join('\n'))
      } else {
        this.$text.html(data['new_html'][this.field])
        this.leave(this)
      }
    }, this))
    .fail($.proxy(function(xhr) {
      this.$mask.hide()
      this.$mask.parents('.popover').hide()
      alert(typeof xhr === 'string' ? xhr : xhr.responseText || xhr.statusText || 'Unknown error!');
    }, this))
}

BrowserPop.prototype.save = function(newValue) {
  this.$form.find('.control-group').removeClass('has-error')
  this.$form.find('.controls .help-block.error').remove()

  this.$mask.show()

  var off_check_box = Object();
  this.$form.find('input[type=checkbox]').each(function(){
    if(!$(this).is(':checked')){
      off_check_box[$(this).attr('name')] = ''
    }
  })

  return $.ajax({
    data: [this.$form.serialize(), $.param(off_check_box)].join('&'),
    url: this.$form.attr('action'),
    type: "POST",
    dataType: 'json',
    beforeSend: function(xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", $.getCookie('csrftoken'))
    }
  })
}

// POPOVER PLUGIN DEFINITION
// =========================

var old = $.fn.browserpop

$.fn.browserpop = function (option) {
  return this.each(function () {
    var $this   = $(this)
    var data    = $this.data('bs.browserpop')
    var options = typeof option == 'object' && options

    if (!data) $this.data('bs.browserpop', (data = new BrowserPop(this, options)))
    if (typeof option == 'string') data[option]()
  })
}

$.fn.browserpop.Constructor = BrowserPop


// POPOVER NO CONFLICT
// ===================

$.fn.browserpop.noConflict = function () {
  $.fn.browserpop = old
  return this
}

$(function(){
  $('.browserable-handler').browserpop();
})

}(window.jQuery);
