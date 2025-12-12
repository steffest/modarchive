let Range = (config)=>{
    let me = {};

    config = config || {};
    let hasInput;

    let elm = document.createElement("div");
    elm.classList.add("range");

    let bar = document.createElement("div");
    bar.classList.add("bar");
    elm.appendChild(bar);

    let progress = document.createElement("div");
    progress.classList.add("progress");
    bar.appendChild(progress);

    let input = document.createElement("input");
    input.type = "range";
    input.min = 0;
    input.max = 100;
    input.value = config.value || 0;
    elm.appendChild(input);

    input.onpointerdown = (e) => {
        hasInput = true;
    }

    input.onpointerup= (e) => {
        hasInput = false;
        if (config && config.onChange){
            config.onChange();
        }
    }

    input.oninput = (e) => {
        let percent = (input.value - input.min) / (input.max - input.min) * 100;
        progress.style.width = percent + "%";
        if (config.onInput) config.onInput();
    }

    me.setValue = function(value){
        if (value>input.max) value = value % input.max;
        input.value = value;
        let percent = (input.value - input.min) / (input.max - input.min) * 100;
        progress.style.width = percent + "%";
    }

    me.getValue = function(){
        return parseInt(input.value);
    }

    me.setMax = function(value){
        input.max = value;
    }

    me.hasInput = function() {
        return hasInput;
    }

    me.onInput = (e) => {
        if (config.onInput) config.onInput();
    }


    me.elm = elm;

    return me;
}

export default Range