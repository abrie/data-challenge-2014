//!!!Getting the width and height from the d3.node() attribute does not work in Firefox
//!!!USE: document.getElementById("dummy_text").getBBox() for the measurements!!!

function text_object(text_rep){
	//initial variables
	this.str_ = '', this.font_size = 20, this.text_object = text_rep, this.scale_=null, this.dy = '.88em';
	var text_height=0, text_width =0, lines = 1;

	//BASIC FUNCTIONS
	//+++++++++++++++
	this.setContent = function(content){
		this.str_ = content;
		this.text_object.text(this.str_)
	}
	this.getContent = function(){return this.str_}
	this.getFontSize = function(){return this.font_size}
	this.getHeight = function(){return text_height}
	this.setFontSize=function(fontsize){
		this.font_size = fontsize;
		this.text_object.attr('font-size',this.font_size+'pt').attr('dy',this.dy)
		this.check_text_dimensions();

	}
	//+++++++++++++++
	//TRANSFORMING FUNCTIONS
	//+++++++++++++++
	this.scale=function(width_, height_){
		//get the scaling parameters
		this.scale_ = this.getScale(width_, height_);
		//transform (scale) svg-text element
		this.text_object.attr('transform',"scale("+this.scale_.a+","+this.scale_.b+")");
	}
	this.wrap=function(width){
		var total_ = 0, counter = 1;
		//get an array - representation of the text
		var raw_text = this.str_.split('');
		//select the svg container
		var svg_ = d3.select('svg');
		//for each letter in the array
		for(var i =0; i<raw_text.length; i++){
			//dummy svg-text element, to...
			var letter = svg_.append('text').attr('font-size',this.font_size+'pt').attr('id','dummy_text').text(this.str_[i]);
			//...get the size of each letter-representation
			total_=total_ + document.getElementById("dummy_text").getBBox().width;	//letter.node().clientWidth;
			//if the letters are too long for the box...
			if(total_>=width){
				total_=0;					//...reset total length
				counter = counter +1;		
				raw_text.splice(i,0,'_')	//...add a separator
			}
			//remove the dummy svg-text element
			letter.remove();
		}
		//make a STRING of the 'text array'
		var text_='';
		raw_text.forEach(function(d){text_=text_+d;})

		//wrap the visual representation of the text
		this.wrapTextObject(text_);
		lines = counter;
	}
	this.wrapTextObject=function(content){
		//split the text at the separator
		var t_wrapped = content.split('_');
			//loop the parts
			if(t_wrapped.length>1){
				//the first line is 'our' normal svg-text element
				text_rep.text(t_wrapped[0])
				//all following lines are a svg-text-tspan element
				for(var i=1;i<t_wrapped.length;i++){
					this.text_object.append('tspan').attr('x',0).attr('dy','.85em').attr('y',text_height*i).text(t_wrapped[i])					
				}
			}
	}
	this.wrap_and_scale=function(box_){
		//1st...wrap it
		this.wrap(box.x);
		//2nd...scale it
		this.scale(box.x, box.y);
	}
	this.scaleFontSizeToBox=function(width_, height_){
		//get the scaling parameters
		this.scale_ = this.getScale(width_, height_);
		//scale font size to scaling parameter a
		this.setFontSize(this.font_size * this.scale_.a);
	}
	this.resetText=function(fontsize){
		this.text_object.attr('transform',"scale(1,1)");
		this.setFontSize(fontsize);
	}
	//+++++++++++++++
	//CALCULATING FUNCTIONS
	//+++++++++++++++
	this.check_text_dimensions = function(){
		text_width = document.getElementById("text_rep").getBBox().width;	//this.text_object.node().offsetWidth;
		text_height = document.getElementById("text_rep").getBBox().height;	//this.text_object.node().offsetHeight;
	}	
	this.getScale=function (width_, height_){
		this.check_text_dimensions();

		var a = width_/text_width;
		var b = height_/text_height;
		
		return {a:a, b:b};
	}	
}