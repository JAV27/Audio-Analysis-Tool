const RegionsPlugin = window.WaveSurfer.regions;
const MAIN_REGION_COLOR = "rgba(232, 184, 12, .5)";
const SPEAKERCOLORS = ["rgba(18, 97, 224,.5)", "rgba(142, 18, 224,.5)", "rgba(204, 201, 53,.5)","rgba(39, 230, 226,.5)","rgba(156, 40, 62,.5)"]

let parsed_regions = null
let dia_regions = []

function OverlayRegions(regions, wavesurfer, vad_regions) {

    for (let i=0;i<vad_regions.length;i++) {
        vad_regions[i].remove()
    }

    for(let i=0; i<regions.length; i++) {
        let w = wavesurfer.addRegion({start:regions[i]["Start Total Seconds"], end:regions[i]["End Total Seconds"], drag:false, resize: false, color: SPEAKERCOLORS[regions[i]["Label"]]});
        dia_regions.push(w)
    }

}

if(regions != null) {
    parsed_regions = JSON.parse(regions.replaceAll("&#34;", '"'))
}

if(fpath != null) {

    let split_path = fpath.split("/")
    $("h2.playing").append(split_path[split_path.length-1])

    let wavesurfer = WaveSurfer.create({
        container: "#audio_player",
        height: 200,
        normalize: true,
        progressColor: "#34a1eb",
        plugins: [
            WaveSurfer.regions.create({})
        ]
    });
    
    let manually_added_region = null
    let vad_regions = []

    wavesurfer.load(fpath);

    for (let i = 0; i < parsed_regions.length; i++) {
        let w = wavesurfer.addRegion({start:parsed_regions[i]["Start Total Seconds"], end:parsed_regions[i]["End Total Seconds"], drag:false, resize: false, color: "rgba(65, 181, 79,.5)"})
        vad_regions.push(w)
    }

    wavesurfer.on("region-created", function(e) {
        manually_added_region = e
    }); 

    wavesurfer.on("region-update-end", function(e) {
        wavesurfer.disableDragSelection();
    }); 

    const regionOptions = {
        "color": MAIN_REGION_COLOR
    }

    $(document).ready(function() {
        $("button.play-icon").click(function(e) {
            audio_state = this.className.split(" ")[1]
            
            if (audio_state == "paused") {
                $(this).removeClass("paused")
                $(this).addClass("playing")
                $("img.pause").show()
                $("img.play").hide()
            } else if (audio_state == "playing") {
                $(this).removeClass("playing")
                $(this).addClass("paused")
                $("img.play").show()
                $("img.pause").hide()
            }
    
            wavesurfer.playPause()    
        });    

        $("button.add").click(function(e) {
        
            wavesurfer.enableDragSelection(regionOptions);

            $(this).prop("disabled", true)
            $(this).addClass("disabled")
            $("button.remove").prop("disabled", false)
            $("button.remove").removeClass("disabled")

        });

        $("button.remove").click(function(e) {
            manually_added_region.remove()
            $("button.add").prop("disabled", false)
            $("button.add").removeClass("disabled")
            wavesurfer.enableDragSelection(regionOptions);
            $(this).prop("disabled", true)
            $(this).addClass("disabled")
        });

        $("button.addRegion").click(function(e) {
            manually_added_region = null
            $("button.add").prop("disabled", false)
            $("button.add").removeClass("disabled")
            $("button.remove").prop("disabled", true)
            $("button.remove").addClass("disabled")
            wavesurfer.disableDragSelection();
        });

        $("button.segmentation").click(function(e) {
            $("#audio_player").hide()
            $(".loader").css({"display":"flex"})

            $.getJSON('/segmentation',
            {
                fpath: fpath,
                regions: regions,
            },
            function(data) {

                $(".loader").hide()
                $("#audio_player").show()

                for(let i=0;i<dia_regions.length;i++) {
                    dia_regions[i].remove()
                }

                dia_regions = []

                OverlayRegions(data, wavesurfer, vad_regions)

            });

        });

    });
    
}

$(document).ready(function() {
    $('.file-input').on("change", function(e) {

        let filename = "No file selected"

        if(e.target.files.length > 0) {
            filename = e.target.files[0].name
        }
        
        $('form p').html(filename)
        $('.submit').show()
    })
})
