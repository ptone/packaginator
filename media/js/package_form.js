function package_form(data){
	var get_slug_from_repo_data = function (repo_root_url, repo_branch_url) {
		var slug = null;
		for (i=0;i<data.length;i++) {
			if (data[i].url == repo_root_url) {
				var regexp_title = new RegExp(data[i].repo_regex);
				var match_obj = regexp_title.exec(repo_branch_url);
				if (match_obj !== null) {
					slug = match_obj[1]
				}
				break;
			}
		}
		return slug;
	}
	var REPLACEMENTS = {
		'https://github.com': [
			'http://github.com',
			'git@github.com:',
			'git://github.com'
		],
		'https://bitbucket.org': [
			'http://bitbucket.org'
		],
		'https://code.launchpad.net/': [
			'lp:'
		]
	};
	
	var repo_url = $("#id_repo_url");
	
	String.prototype.starts_with = function(str){
		return (this.indexOf(str) === 0);
	}
	
	String.prototype.ends_with = function(str){
		return (this.lastIndexOf(str) === this.length-str.length);
	}
	
	repo_url.focus();
	
	
	
	
	repo_url.keyup(function(e) {
		var url = repo_url.val();
		return url
	});
		
	repo_url.change(function(e) {
	 
		$("#target").text(repo_url.val());
		
		var url = repo_url.val();
		
		// this fixes the problem with trailing slashes
		while (1==1){
			if (url.ends_with('/')){
				url = url.slice(0, url.length-1);
				repo_url.val(url);
				}
			else {
				break;
			};
		};
		
		$.each(REPLACEMENTS, function(key, value){
			$.each(value, function(index, prefix){
				if (url.starts_with(prefix)){
					url = key + url.slice(prefix.length);
				}
            });
		});
		if (url.ends_with('.git')){
			url = url.slice(0, url.length-4);
			repo_url.val(url);				
		};
		repo_url.val(url);
		
		var url_array = url.split('/');
		$.each(data, function(index, item) {
			if (url.starts_with(item.url)){
				if (url !== item.url){
					var slug = null;
					if ($("#id_title").val().length === 0) {
						// determine title/slug automagically
						slug = get_slug_from_repo_data(item.url, url);
						$("#id_title").val(slug);
					};
					if (slug === null) {
						// fallback slug detector
						slug = DPSlugify(url_array[url_array.length-1]);
					}
					$("#id_slug").val(slug);
					pypi_url.val(slug);
					$("#package-form-message").text("Your package is hosted at " + item.title)
				};
			};
		});
	});
