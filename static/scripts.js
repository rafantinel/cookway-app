$(function() {

    // Mobile menu button
    $(".btn-mobile").click(function() {
        $(".menu-mobile").slideToggle();
    });

    // Close menu when resizing
    $(window).resize(function() {
        if ($(".menu-mobile").is(":visible")) {
            $(".menu-mobile").css("display", "none")
        }
    });

    // Password hint
    $("input[name='password']").focus(function() {
        $(".text-muted").removeClass("d-none");
    });

    // Remove invalid warning
    $(".form-control").change(function() {
        if ($(".is-invalid").is(":visible")) {
            $(".is-invalid").remove();
        }
    });

    // File input style
    $(".file-input-layout").click(function() {
        $(this).parent().children().closest(".file-input").click();
    });

    // File input style
    $(".file-input").change(function() {
        $(this).parent().children().closest(".file-input-layout").css("padding", ".375rem .75rem");
        // $(".file-input-dishes, .file-input-profile").css("padding", ".375rem .75rem");
        var filename = $(this).val().split("\\").pop();
        if (filename != "") {
            $(this).parent().children().closest(".file-input-layout").html(filename);
        } else {
            $(this).parent().children().closest(".file-input-layout").html("Inserir Imagem");
        }
    });

    // Delete dish or menu
    $(".fa-trash").click(function(e) {
        $(".message-delete").removeClass("d-none");
        $(".screen-filter").removeClass("d-none");

        var deleteId = $(this).parent().next().children().closest("span").attr("value");

        if ($(this).parents().eq(3).hasClass("table-dishes")) {
            $(".message-delete form").attr("action", "/pratos?deletar_prato=" + deleteId);
        } else {
            $(".message-delete form").attr("action", "/pratos?deletar_menu=" + deleteId);
        }

        e.stopPropagation();
    });

    // Cancel delete button
    $(".cancel-delete").click(function() {
        $(".message-delete").addClass("d-none");
        $(".screen-filter").addClass("d-none");
    });

    // Redirect after clicking message box
    $(".delete-error").click(function() {
        $(".message-delete").addClass("d-none");
        $(".screen-filter").addClass("d-none");
        location.href = location.href.split("/").pop().split("?")[0];
    });

    // Prevent form or messages from closing
    $(".form-container-dishes, .form-container-menus, .message-delete").click(function(e) {
        e.stopPropagation();
    });

    // Ingredients global variables
    var ingredientCounter = 0;
    var ingredients = [];
    var input = $("input[name='name_ingredients_dish']");
    var ingredientsBox = $(".ingredients-box");

    // Add dishes
    $(".add-dish-btn").click(function (e) {
        $(".form-container-dishes").removeClass("d-none");
        $(".screen-filter").removeClass("d-none");
        $(".form-container-dishes h3").html("Adicionar Prato");
        $(".submit-dishes").html("Adicionar");
        $(".dishes-form").attr("action", "/pratos?adicionar_prato=1");
        $(".dishes-form").addClass("add-dishes-active");
        $(".update-dishes-active small").remove();
        $(".dishes-form").removeClass("update-dishes-active");
        $("input.form-control").val("");
        $(".file-input-dishes").html("Inserir Imagem");
        $(".file-input-dishes").css("padding", ".375rem .75rem");
        ingredientsBox.attr("hidden", "");

        if (ingredientCounter > 0) {
            ingredientCounter = 0;
            ingredients = [];
            ingredientsBox.html("");
        }
        
        e.stopPropagation();
    });

    // Update dishes
    $(".table-dishes .fa-pen").click(function(e) {
        $(".form-container-dishes").removeClass("d-none");
        $(".screen-filter").removeClass("d-none");
        $(".form-container-dishes h3").html("Editar Prato");
        $(".submit-dishes").html("Alterar");
        dishId = $(this).parent().parent().children().eq(1).children().attr("value");
        getCurrentId = location.href.split("=").pop();
        if (dishId != getCurrentId) {
            $(".dishes-form small").remove();
        }
        $(".dishes-form").attr("action", "/pratos?atualizar_prato=" + dishId);
        $(".dishes-form").addClass("update-dishes-active");
        $(".add-dishes-active small").remove();
        $(".dishes-form").removeClass("add-dishes-active");

        if (ingredientCounter > 0) {
            ingredientCounter = 0;
        }

        $("input[name='name_dish']").val($("#dishName_" + dishId).html());
        $("input[name='description_dish']").val($("#dishDescription_" + dishId).html());
        $(".form-container-dishes option").each(function() {
            if ($(this).attr("value") == $("#dishType_" + dishId).attr("value")) {
               $(this).attr("selected", "");
            } else if ($(this).attr("selected")) {
                 $(this).removeAttr("selected");
            }
        });

        ingredientsBox.html("");
        ingredientsBox.removeAttr("hidden");

        $("#dishIngredients_" + dishId + " option").each(function() {
            if ($(this).html() != "Ingred.") {
                ingredientsBox.append("<span>" + $(this).html() + "</span>");
            }
        });

        ingredientCounter = $("#dishIngredients_" + dishId + " option").length - 1;

        $("input[name='price_dish']").val($("#dishPrice_" + dishId).attr("value"));
        
        if ($("#dishImage_" + dishId + " img").attr("src") != "/static/food-dish.png") {
            $(".file-input-dishes").html($("#dishImage_" + dishId).html());
            $(".file-input-dishes").css("padding", "0");
        } else {
            $(".file-input-dishes").html("Inserir Imagem");
            $(".file-input-dishes").css("padding", ".375rem .75rem");
        }

        e.stopPropagation();

    });

    // Update input values
    update_dishes_form();
    function update_dishes_form() {
        let form = $(".dishes-form");
        if (form.attr("action")) {
            let currentForm = form.attr("action").split("?")[1].split("=")[0];
            if (currentForm == "adicionar_prato") {
               $(".add-dish-btn").click();
            } else if (currentForm == "atualizar_prato") {
                let dishId = form.attr("action").split("=").pop();
                $("#dishId_" + dishId).parent().parent().children().first().children().closest(".fa-pen").click();
            }
        }
    }

    // Close current form
    $(".close-btn").click(function() {
        if ($(".message-delete, .form-container-dishes, .form-container-menus").is(":visible")) {
            $(".message-delete").addClass("d-none");
            $(".form-container-dishes").addClass("d-none");
            $(".form-container-menus").addClass("d-none");
            $(".screen-filter").addClass("d-none");
        }
    });

    // Add ingredient
    $(".btn-add-ingredient").click(function() {
        if (input.val() != "" && ingredientCounter < 13) {
            if (ingredientsBox.is(":hidden")) {
                ingredientsBox.removeAttr("hidden");
            }
            ingredientsBox.append("<span>"+ input.val().replace(/_/g, "") +"</span>");
            input.val("");
            ingredientCounter ++;
        } else if (ingredientCounter == 13) {
            alert("É possível adicionar no máximo 12 ingredientes!");
        }
        return false;
    });

    // Remove ingredient
    $(".btn-remove-ingredient").click(function() {
        var lastElem = ingredientsBox.children().last();
        if (lastElem.length > 0) {
            lastElem.remove();
            ingredientCounter --;
        }
        
        if (ingredientCounter == 0 && ingredientsBox.is(":visible")) {
            ingredientsBox.attr("hidden","");
        }

        return false;
    });

    // Submit ingredients and dishes
    $(".dishes-form").on("submit", function() {

        ingredients = [];
        count = 0;
        $(".ingredients-box span").each(function(){
            ingredients.push($(this).html());
        });

        var value = "";
        for (var i = 0; i < ingredients.length; i++) {
            if (i < ingredients.length - 1) {
                value = value + ingredients[i] + "_";
            } else {
                value = value + ingredients[i];
            }
        }

        if (ingredientCounter > 0) {
            ingredientsBox.attr("hidden","");
            ingredientsBox.html("");
            ingredientCounter = 0;
            ingredients = [];
            input.val(value);
        }

    });

    // Add menus
    $(".add-menu-btn").click(function(e) {
       $(".form-container-menus").removeClass("d-none");
       $(".screen-filter").removeClass("d-none");
       $(".menus-form").attr("action", "/pratos?adicionar_menu=1");
       $(".menus-form").addClass("add-menus-active");
       $(".update-menus-active small").remove();
       $(".menus-form").removeClass("update-menus-active");

       e.stopPropagation();
    });

    // Update menus
    $(".table-menus .fa-pen").click(function(e) {
        $(".form-container-menus").removeClass("d-none");
        $(".screen-filter").removeClass("d-none");
        $(".form-container-menus h3").html("Editar Menu");
        $(".submit-menus").html("Alterar");
        menuId = $(this).parent().parent().children().eq(1).children().attr("value");
        getCurrentId = location.href.split("=").pop();
        if (menuId != getCurrentId) {
            $(".menus-form small").remove();
        }
        $(".menus-form").attr("action", "/pratos?atualizar_menu=" + menuId);
        $(".menus-form").addClass("update-menus-active");
        $(".add-menus-active small").remove();
        $(".menus-form").removeClass("add-menus-active");

        $("input[name='name_menu']").val($("#menuName_" + menuId).html());
        $("input[name='description_menu']").val($("#menuDescription_" + menuId).html());
        $(".form-container-menus option").each(function() {
            optionValue = $(this).attr("value");
            entryValue = $("#menuEntry_" + menuId).attr("value");
            mainValue = $("#menuMain_" + menuId).attr("value");
            dessertValue = $("#menuDessert_" + menuId).attr("value");
            
            if (optionValue == entryValue) {
                $(this).attr("selected", "");
            } else if (optionValue == mainValue) {
                $(this).attr("selected", "");
            } else if (optionValue == dessertValue) {
                $(this).attr("selected", "");
            } else {
                $(this).removeAttr("selected");
            }
            
        });
        $("input[name='price_menu']").val($("#menuPrice_" + menuId).attr("value"));
        

        e.stopPropagation();

    });

    // Update input values
    update_menus_form();
    function update_menus_form() {
        let form = $(".menus-form");
        if (form.attr("action")) {
            let currentForm = form.attr("action").split("?")[1].split("=")[0];
            if (currentForm == "adicionar_menu") {
               $(".add-menu-btn").click();
            } else if (currentForm == "atualizar_menu") {
                let menuId = form.attr("action").split("=").pop();
                $("#menuId_" + menuId).parent().parent().children().first().children().closest(".fa-pen").click();
            }
        }
    }

    // Redirect after clicking message box
    $(".message-request-btn").click(function() {
        $(".message-request-error").remove();
        $(".screen-filter").addClass("d-none");
        location.href = location.href.split("/").pop().split("?")[0];
    });

    // File input style
    if ($(".file-input-profile").find("img").length > 0) {
        $(".file-input-profile").css("padding", "0");
    } else {
        $(".file-input-profile").css("padding", ".375rem .75rem");
    }

    // IBGE Api
    $.getJSON('https://servicodados.ibge.gov.br/api/v1/localidades/estados/', {id: 10, }, function (json) {
 
        var options = '<option value="">Estado</option>';
 
        for (var i = 0; i < json.length; i++) {
 
            options += '<option data-id="' + json[i].id + '" value="' + json[i].sigla + '" >' + json[i].nome + '</option>';
 
        }
 
        $("select[name='state_search']").html(options);
        $("select[name='city_search']").html('<option value="">Cidade</option>');
        $("select[name='state_search']").change(function () {
            if ($(this).val()) {
                $.getJSON('https://servicodados.ibge.gov.br/api/v1/localidades/estados/'+$(this).find("option:selected").attr('data-id')+'/municipios', {id: $(this).find("option:selected").attr('data-id')}, function (json) {
     
                    var options = '<option value="">Cidade</option>';
     
                    for (var i = 0; i < json.length; i++) {
     
                        options += '<option value="' + json[i].nome + '" >' + json[i].nome + '</option>';
     
                    }
     
                    $("select[name='city_search']").html(options);
     
                });
     
            } else {
     
                $("select[name='city_search']").html('<option value="">Cidade</option>');
            }
        });
 
    });

});
